from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy  
from config import Config
import os

db = SQLAlchemy()


def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    templates_path = os.path.join(base_dir, '..', 'templates')

    app = Flask(__name__, template_folder=templates_path)
    app.config.from_object(Config)

    db.init_app(app)

    
    global migrate
    migrate = Migrate(app, db)

    from app.routes import main
    app.register_blueprint(main)

    return app