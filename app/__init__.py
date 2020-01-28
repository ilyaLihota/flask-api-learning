from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)

    # Register blueprints
    from app.api_1_0 import api
    app.register_blueprint(api, url_prefix='/api/v1.0')

    return app
