import pytest
from paralympics import create_app


@pytest.fixture()
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    # TODO: Add data to the database

    yield app

    # clean up / reset resources


@pytest.fixture()
def client(app):
    return app.test_client()