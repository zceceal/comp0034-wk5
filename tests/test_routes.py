def test_get_regions_status_code(client):
    """
    GIVEN a Flask test client
    WHEN a request is made to /regions
    THEN the status code should be 200
    """
    response = client.get("/regions")
    assert response.status_code == 200


def test_get_regions_json(client):
    """
    GIVEN a Flask test client
    AND the database contains data of the regions
    WHEN a request is made to /regions
    THEN the response should contain json
    AND a JSON object for Zimbabwe should be in the json
    """
    response = client.get("/regions")
    assert response.headers["Content-Type"] == "application/json"
    zimbabwe = {'NOC': 'ZIM', 'notes': None, 'region': 'Zimbabwe'}
    assert zimbabwe in response.json


# Test if one can add data to the database
def test_add_bookmark():
    my_data = {
        "title": 'a unique title',
        "description": 'a bookmark description',
        "url": 'unique bookmark url',
    }
    res = app.test_client().post(
        "/bookmark/",
        data=json.dumps(my_data),
        content_type="application/json",
    )
    assert res.status_code == 201