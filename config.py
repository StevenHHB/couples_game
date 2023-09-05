import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = secrets.token_hex(16)
SQLALCHEMY_DATABASE_URI = 'postgresql://hapyttrvveukpb:3e7f2e1f390a362bc766095b619f3302a642b58430cb9e0310ccc8bcab6f084a@ec2-35-169-9-79.compute-1.amazonaws.com:5432/ddbmbvntauvjls'
SQLALCHEMY_TRACK_MODIFICATIONS = False
