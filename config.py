import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# generate a secret key with secret package

secret_key = secrets.token_hex(16)

SECRET_KEY = '1234567891234567'
