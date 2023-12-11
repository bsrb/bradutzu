from flask import Flask
from config import Config
from sqlalchemy import exc
from sqlalchemy_utils import database_exists
from brad.extensions import ctrl, db
from werkzeug.middleware.proxy_fix import ProxyFix

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

    ctrl.start()

    db.init_app(app)
    from .models import user
    if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
        print('Database does not exist, initializing...')
        with app.app_context():
            try:
                db.create_all()
            except exc.SQLAlchemyError as sqlalchemyerror:
                print(f'SQLAlchemyError: {str(sqlalchemyerror)}')
            except Exception as e:
                print(f'Exception: {str(e)}')
            else:
                print('Database initialized')

    from brad import main
    app.register_blueprint(main.main)

    return app