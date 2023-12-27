from flask import current_app as app, request, make_response
from paralympics import db
from paralympics.models import Region, Event
from paralympics.schemas import RegionSchema, EventSchema

# Flask-Marshmallow Schemas
regions_schema = RegionSchema(many=True)
region_schema = RegionSchema()
events_schema = EventSchema(many=True)
event_schema = EventSchema()


@app.get("/regions")
def get_regions():
    """Returns a list of NOC region codes and their details in JSON.

    :returns: JSON
    """
    # Select all the regions using Flask-SQLAlchemy
    all_regions = db.session.execute(db.select(Region)).scalars()
    # Dump the data using the Marshmallow regions schema; '.dump()' returns JSON.
    result = regions_schema.dump(all_regions)
    # Return the data in the HTTP response
    return result


@app.get('/regions/<code>')
def get_region(code):
    """ Returns one region in JSON.

    :param code: The NOC code of the region to return
    :param type code: str
    :returns: JSON
    """
    # Query structure shown at https://flask-sqlalchemy.palletsprojects.com/en/3.1.x/queries/#select
    region = user = db.session.execute(db.select(Region).filter_by(NOC=code)).scalar_one()
    # Dump the data using the Marshmallow region schema; '.dump()' returns JSON.
    result = region_schema.dump(region)
    # Return the data in the HTTP response
    return result


@app.get("/events")
def get_events():
    """Returns a list of events and their details in JSON.

    :returns: JSON
    """
    all_events = db.session.execute(db.select(Event)).scalars()
    result = events_schema.dump(all_events)
    return result


@app.get('/events/<event_id>')
def get_event(event_id):
    """ Returns the event with the given id JSON.

    :param event_id: The id of the event to return
    :param type event_id: int
    :returns: JSON"""
    event = db.session.execute(db.select(Event).filter_by(id=event_id)).scalar_one()
    result = event_schema.dump(event)
    return result


@app.post('/events')
def add_event():
    """ Adds a new event.

   Gets the JSON data from the request body and uses this to deserialise JSON to an object using Marshmallow
   event_schema.loads()

   :returns: JSON
   """
    ev_json = request.get_json()
    event = event_schema.load(ev_json)
    db.session.add(event)
    db.session.commit()
    return {"message": f"Event added with id= {event.id}"}


@app.post('/regions')
def add_region():
    """ Adds a new region.

    Gets the JSON data from the request body and uses this to deserialise JSON to an object using Marshmallow
   region_schema.loads()

    :returns: JSON"""
    json_data = request.get_json()
    region = region_schema.load(json_data)
    db.session.add(region)
    db.session.commit()
    return {"message": f"Region added with NOC= {region.NOC}"}


@app.delete('/events/<int:event_id>')
def delete_event(event_id):
    """ Deletes the event with the given id.

    :param event_id: The id of the event to delete
    :returns: JSON"""
    event = db.session.execute(db.select(Event).filter_by(id=event_id)).scalar_one()
    db.session.delete(event)
    db.session.commit()
    return {"message": f"Event {event_id} deleted"}


@app.delete('/regions/<noc_code>')
def delete_region(noc_code):
    """ Deletes the region with the given code.

    :param code: The NOC code of the region to delete
    :returns: JSON"""
    region = db.session.execute(db.select(Region).filter_by(NOC=noc_code)).scalar_one()
    db.session.delete(region)
    db.session.commit()
    return {"message": f"Region {noc_code} deleted"}


@app.patch("/events/<event_id>")
def event_update(event_id):
    """Updates changed fields for the event.

    """
    # Find the event in the database
    existing_event = db.session.execute(
        db.select(Event).filter_by(event_id=event_id)
    ).scalar_one_or_none()
    # Get the updated details from the json sent in the HTTP patch request
    event_json = request.get_json()
    # Use Marshmallow to update the existing records with the changes from the json
    event_update = event_schema.load(event_json, instance=existing_event, partial=True)
    # Commit the changes to the database
    db.session.add(event_update)
    db.session.commit()
    # Return json showing the updated record
    updated_event = db.session.execute(
        db.select(Event).filter_by(event_id=event_id)
    ).scalar_one_or_none()
    result = event_schema.jsonify(updated_event)
    response = make_response(result, 200)
    response.headers["Content-Type"] = "application/json"
    return response


@app.patch("/regions/<noc_code>")
def region_update(noc_code):
    """Updates changed fields for the region.

    """
    # Find the region in the database
    existing_region = db.session.execute(
        db.select(Region).filter_by(NOC=noc_code)
    ).scalar_one_or_none()
    # Get the updated details from the json sent in the HTTP patch request
    region_json = request.get_json()
    # Use Marshmallow to update the existing records with the changes from the json
    region_update = region_schema.load(region_json, instance=existing_region, partial=True)
    # Commit the changes to the database
    db.session.add(region_update)
    db.session.commit()
    # Return json showing the updated record
    updated_region = db.session.execute(
        db.select(Region).filter_by(NOC=noc_code)
    ).scalar_one_or_none()
    result = region_schema.jsonify(updated_region)
    response = make_response(result, 200)
    response.headers["Content-Type"] = "application/json"
    return response
