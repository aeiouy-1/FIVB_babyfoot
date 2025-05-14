import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'monmotdepasse')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///babyfoot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
