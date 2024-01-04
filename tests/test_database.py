# A test that includes using a context to check the database
from sqlalchemy import func
from paralympics import db
from paralympics.models import Region


def test_post_region_database_update(client, app):
    """
    GIVEN a Flask test client and test app
    AND valid JSON for a new region
    WHEN a POST request is made to /regions
    THEN the database should have one more entry
    """
    region_json = {"NOC": "ZBZ", "region": "ZedBeeZed"}

    # Count the rows in the Region table before and after the post
    with app.app_context():
        num_rows_start = db.session.scalar(db.select(func.count(Region.NOC)))
        client.post("/regions", json=region_json)
        num_rows_end = db.session.scalar(db.select(func.count(Region.NOC)))
    assert num_rows_end - num_rows_start == 1