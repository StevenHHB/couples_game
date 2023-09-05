import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = secrets.token_hex(16)
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
SQLALCHEMY_TRACK_MODIFICATIONS = False
