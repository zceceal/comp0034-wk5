import os
from pathlib import Path

import pytest
from sqlalchemy import exists
from paralympics import create_app, db
from paralympics.models import Region
from paralympics.schemas import RegionSchema


@pytest.fixture(scope='session')
def app():
    """Fixture that creates a test app.

    The app is created with test config parameters that include a temporary database. The app is created once for
    each test module.

    Returns:
        app A Flask app with a test config

    """
    # See https://flask.palletsprojects.com/en/2.3.x/tutorial/tests/#id2
    # Create a temporary testing database
    db_path = Path(__file__).parent.parent.joinpath('data', 'paralympics_testdb.sqlite')
    test_cfg = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(db_path),
    }
    app = create_app(test_config=test_cfg)

    yield app

    # clean up / reset resources
    # Delete the test database (if adding data to your database takes a long time you may prefer not to delete the
    # database)
    os.unlink(db_path)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def new_region(app):
    """Create a new region and add to the database.

    Adds a new Region to the database and also returns the JSON for a new region.
    """
    new_region_json = {'NOC': 'NEW', 'notes': None, 'region': 'A new region'}

    with app.app_context():
        region_schema = RegionSchema()
        new_region = region_schema.load(new_region_json)
        db.session.add(new_region)
        db.session.commit()

    yield new_region_json

    # Remove the region from the database at the end of the test if it still exists
    with app.app_context():
        region_exists = db.session.query(exists().where(Region.NOC == 'NEW')).scalar()
        if region_exists:
            db.session.delete(new_region)
            db.session.commit()
