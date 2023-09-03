from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Assuming 'app' and 'db' are your Flask and SQLAlchemy instances respectively


db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    db.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)

    with app.app_context():
        from . import routes, models  # Import routes after the app is created
        db.create_all()  # Optionally, create all tables here

    return app
