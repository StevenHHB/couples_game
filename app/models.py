from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy import or_


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True,
                         nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(128), nullable=False)
    profile_picture = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_couple(self):
        couple = Couple.query.filter(
            or_(Couple.user1_id == self.id,
                Couple.user2_id == self.id),
            Couple.status == RelationshipStatus.ACCEPTED
        ).first()
        return couple

    def get_current_game_session(self):
        # Fetch and return the current game session for the user's couple
        couple = self.get_couple()
        if couple:
            current_game_session = couple.get_current_game_session()
            return current_game_session
        return None

    def get_game_session_history(self):
        # Fetch and return the game session history for the user's couple
        couple = self.get_couple()
        if couple:
            game_session_history = couple.get_game_session_history()
            return game_session_history
        return None

    def get_user_click_count(self):
        current_game_session = self.get_current_game_session()
        if current_game_session:
            if self == current_game_session.couple.user1:
                return current_game_session.click_count_user1
            elif self == current_game_session.couple.user2:
                return current_game_session.click_count_user2
        return 0


class RelationshipStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Couple(db.Model):
    __tablename__ = 'couple'

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey(
        'user.id', name="fk_couple_user1_id"), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey(
        'user.id', name="fk_couple_user2_id"), nullable=False)
    status = db.Column(db.Enum(RelationshipStatus),
                       default=RelationshipStatus.PENDING)

    user1 = db.relationship('User', foreign_keys=[
                            user1_id], backref="user1_couples")
    user2 = db.relationship('User', foreign_keys=[
                            user2_id], backref="user2_couples")

    def get_current_game_session(self):
        # Fetch and return the current game session for the couple
        current_game_session = CouplesGameSession.query.filter_by(
            couple_id=self.id).order_by(CouplesGameSession.start_time.desc()).first()
        return current_game_session

    def get_game_session_history(self):
        # Fetch and return the game session history for the couple
        game_session_history = CouplesGameSessionHistory.query.filter_by(
            couple_id=self.id).order_by(CouplesGameSessionHistory.start_time.desc()).all()
        return game_session_history


class CouplesGameSession(db.Model):
    __tablename__ = 'couples_game_session'

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey(
        'couple.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    click_count_user1 = db.Column(db.Integer, default=0)
    click_count_user2 = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="ACTIVE")

    couple = db.relationship('Couple', backref='game_sessions')


class CouplesGameSessionHistory(db.Model):
    __tablename__ = 'couples_game_session_history'

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey(
        'couple.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    click_count_user1 = db.Column(db.Integer, nullable=False)
    click_count_user2 = db.Column(db.Integer, nullable=False)

    couple = db.relationship('Couple', backref='game_session_histories')
