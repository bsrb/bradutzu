from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

class Config:
    # General config
    FLASK_ENV = environ.get('ENVIRONMENT')
    FLASK_APP = environ.get('FLASK_APP')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    DEBUG = environ.get('DEBUG') is not None

    MAX_ANIM_PER_USER = 3

    # Controller
    NUMBER_OF_PIXELS = 100
    ANIMATION_FOLDER = 'animations'
    ANIMATION_RUN_TIME = 180
    TEST_RUN_TIME = 30

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + path.join(basedir, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
