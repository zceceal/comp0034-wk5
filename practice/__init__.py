import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


# https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/quickstart/
class Base(DeclarativeBase):
    pass


# First create the db object using the SQLAlchemy constructor.
# Pass a subclass of either DeclarativeBase or DeclarativeBaseNoMeta to the constructor.


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        # Generate your own SECRET_KEY using python secrets
        SECRET_KEY='lCtirPCf1S44mWAGoWqxlA',
        # configure the SQLite database, relative to the app instance folder
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, 'practice.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialise Flask with the SQLAlchemy database extension

    # Models are defined in the models module, so you must import them before calling create_all, otherwise SQLAlchemy
    # will not know about them.

    # Create the tables in the database

    return app
