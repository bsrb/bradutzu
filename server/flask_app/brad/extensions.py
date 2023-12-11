from flask_sqlalchemy import SQLAlchemy
from .controller.controller import Controller
from config import Config

db = SQLAlchemy()
ctrl = Controller(Config)