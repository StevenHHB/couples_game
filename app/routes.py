from flask import render_template
from flask_login import LoginManager, login_required
from flask import render_template, redirect, url_for, request, flash, jsonify, session
# Change the imports here
from app.models import db, User, Couple, RelationshipStatus, CouplesGameSession, CouplesGameSessionHistory
from flask import current_app as app
from flask_login import login_user, current_user, logout_user
from sqlalchemy import or_
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app import create_app

login_manager = LoginManager()

# Initialize the login manager within the app context
with app.app_context():
    login_manager.init_app(app)

scheduler = BackgroundScheduler(timezone="UTC")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# basic endpoints


@app.route('/')
def home():
    # If user is authenticated, redirect to profile page
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    # If user is not authenticated, show the login page
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered!')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Registration successful!')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!')
            return redirect(url_for('profile'))

        flash('Invalid email or password.')

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    if not current_user.is_authenticated:
        flash('Please login to access profile.')
        return redirect(url_for('login'))

    pending_requests = Couple.query.filter_by(
        user2_id=current_user.id, status=RelationshipStatus.PENDING).all()

    couple_info = Couple.query.filter(
        or_(Couple.user1_id == current_user.id,
            Couple.user2_id == current_user.id),
        Couple.status == RelationshipStatus.ACCEPTED
    ).first()

    if couple_info:
        if couple_info.user1_id == current_user.id:
            other_user_id = couple_info.user2_id
        else:
            other_user_id = couple_info.user1_id

        other_user = User.query.get(other_user_id)
        # Now 'other_user' contains the User object of the other user in the couple
    else:
        # There is no accepted couple with the current user
        other_user = None

    current_game_session = None
    time_remaining = None
    couple = current_user.get_couple()

    if couple:
        current_game_session = couple.get_current_game_session()

    if current_game_session:
        time_remaining = (current_game_session.start_time +
                          timedelta(minutes=5)) - datetime.utcnow()
    else:
        time_remaining = None

    game_session_history = None
    game_outcomes = None

    if couple:
        game_session_history = couple.get_game_session_history()

        # Calculate game outcomes (win/loss) for each game
        game_outcomes = []
        if game_session_history:
            for game_session in game_session_history:
                if game_session.click_count_user1 > game_session.click_count_user2:
                    if current_user == couple.user1:
                        game_outcomes.append("Won")
                    else:
                        game_outcomes.append("Lost")
                elif game_session.click_count_user1 < game_session.click_count_user2:
                    if current_user == couple.user2:
                        game_outcomes.append("Won")
                    else:
                        game_outcomes.append("Lost")
                else:
                    game_outcomes.append("Tied")

    return render_template('profile.html', user=current_user, pending_requests=pending_requests,
                           other_user=other_user, couple=couple, current_game_session=current_game_session,
                           time_remaining=time_remaining, game_session_history=game_session_history,
                           game_outcomes=game_outcomes)


@app.route('/couple_profile/<int:other_user_id>')
def couple_profile(other_user_id):
    if not current_user.is_authenticated:
        flash('Please login to access the couple profile.')
        return redirect(url_for('login'))

    partner = User.query.get(other_user_id)

    return render_template('couple_profile.html', partner=partner)


# couple related routes
@app.route('/search', methods=['GET', 'POST'])
def search():
    # Assuming you store user's ID in session as 'user_id'
    user_id = current_user.id
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    # If POST request, perform the search
    if request.method == 'POST':
        query = request.form.get('query')
        users = User.query.filter(User.username.ilike(f'%{query}%')).all()
        return jsonify([{"id": user.id, "username": user.username} for user in users])
    # If GET request, render the search page
    return render_template('search.html', user_id=user_id)


@app.route('/add_couple', methods=['POST'])
def add_couple():
    # Assuming you store user's ID in session as 'user_id'
    user1_id = current_user.id

    if not user1_id:
        # Handle cases where there is no logged-in user, e.g., return an error message
        return jsonify({"error": "User not logged in!"}), 401

    user2_id = request.form.get('user2_id')  # User to send request

    # Check if user2_id is valid and exists
    user2 = User.query.get(user2_id)
    if not user2:
        return jsonify({"error": "User not found!"}), 404

    # Prevent sending request to oneself
    if user1_id == user2_id:
        return jsonify({"error": "Can't send a request to yourself!"}), 100

    # Check if there's an existing request
    existing_request = Couple.query.filter(
        (Couple.user1_id == user1_id) & (Couple.user2_id == user2_id) |
        (Couple.user1_id == user2_id) & (Couple.user2_id == user1_id)
    ).first()
    if existing_request:
        return jsonify({"error": "Request already exists!"}), 200

    # Create new couple with PENDING status
    couple = Couple(user1_id=user1_id, user2_id=user2_id,
                    status=RelationshipStatus.PENDING)
    db.session.add(couple)
    db.session.commit()

    return jsonify({"message": "Request sent!"}), 201


@app.route('/accept_request/<int:couple_id>', methods=['POST'])
def accept_request(couple_id):
    if not current_user.is_authenticated:
        flash('Please login to accept the request.')
        return redirect(url_for('login'))

    couple_request = Couple.query.get(couple_id)
    if not couple_request or couple_request.status != RelationshipStatus.PENDING:
        flash('Invalid or expired request.')
        return redirect(url_for('profile'))

    if current_user.id != couple_request.user2_id:
        flash('Unauthorized access.')
        return redirect(url_for('profile'))

    # Check if the user already has an accepted couple
    if Couple.query.filter(
            (Couple.user1_id == current_user.id) & (Couple.status == RelationshipStatus.ACCEPTED) |
            (Couple.user2_id == current_user.id) & (
                Couple.status == RelationshipStatus.ACCEPTED)
    ).first():
        flash('You already have an accepted couple.')
        return redirect(url_for('profile'))

    # Accept the couple request
    couple_request.status = RelationshipStatus.ACCEPTED
    db.session.commit()
    flash('You are now a couple with ' + couple_request.user1.username + '!')
    return redirect(url_for('profile'))


@app.route('/start_game', methods=['POST'])
@login_required
def start_game():
    couple = current_user.get_couple()

    if couple and couple.status == RelationshipStatus.ACCEPTED:
        current_game_session = couple.get_current_game_session()

        if current_game_session is None or current_game_session.status == "ENDED":
            new_game_session = CouplesGameSession(couple=couple)
            db.session.add(new_game_session)
            db.session.commit()
            flash('Game session started! Click away!')
        else:
            flash('You already have an active game session. Keep clicking!')

        return redirect(url_for('profile'))
    else:
        flash(
            'You and your couple need to be in an accepted relationship to start the game.')
        return redirect(url_for('profile'))


@app.route('/click', methods=['POST'])
@login_required
def click():
    couple = current_user.get_couple()
    current_game_session = couple.get_current_game_session()

    if current_game_session:
        if current_user == couple.user1:
            current_game_session.click_count_user1 += 1
        elif current_user == couple.user2:
            current_game_session.click_count_user2 += 1
        db.session.commit()
        flash('Click recorded!')
    else:
        flash('You need to start a game session first.')

    return redirect(url_for('profile'))


def check_and_update_game_sessions():
    app = create_app()
    with app.app_context():
        active_game_sessions = CouplesGameSession.query.filter(
            CouplesGameSession.start_time <= datetime.utcnow() - timedelta(minutes=5),
            CouplesGameSession.status != "ENDED"
        ).all()

        for game_session in active_game_sessions:
            game_session.status = "ENDED"
            game_session.end_time = datetime.utcnow()

            # Create a new game session history entry
            history_entry = CouplesGameSessionHistory(
                couple_id=game_session.couple_id,
                start_time=game_session.start_time,
                end_time=game_session.end_time,
                click_count_user1=game_session.click_count_user1,
                click_count_user2=game_session.click_count_user2
            )
            db.session.add(history_entry)
            db.session.commit()

            # Delete the current game session
            db.session.delete(game_session)
            db.session.commit()


scheduler.add_job(
    check_and_update_game_sessions,
    trigger=IntervalTrigger(seconds=1),  # Adjust the interval as needed
    id='check_and_update_game_sessions',
    name='Check and Update Game Sessions Job'
)

scheduler.start()
