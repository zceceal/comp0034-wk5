# Handling errors / exceptions

Last week there were some tests that failed as error handling had not yet been added to the app.

In a REST API, you want the results of any HTTP request to return JSON (or other format) as that is what the users will
be expecting in their application code. This activity therefore focuses on handling errors and returning any messages in
JSON format. There are tutorials for Flask that focus on HTML pages returned for errors, we will consider these in the
second part of the course, but not for the REST API.

In this activity you will:

1. Use the logger to track events while the server is being used (useful for debugging)
2. Configure Flask to handle generic errors and return JSON
3. Use Python try/except in the routes e.g. to handle errors with database requests

## 1. Use logging to track events in a running Flask app

You can use logging to track events that happen when the server is running and the application is being used. This
can make troubleshooting errors easier as helps you see what is going on in your application.

With logging, you can use different functions to report information on different logging levels. Each level indicates an
event happened with a certain degree of severity. The following functions can be used:

- app.logger.debug(): For detailed information about the event.
- app.logger.info(): Confirmation that things are working as expected.
- app.logger.warning(): Indication that something unexpected happened (such as “disk space low”), but the application is
  working as expected.
- app.logger.error(): An error occurred in some part of the application.
- app.logger.critical(): A critical error; the entire application might stop working.

You can add these to your code. For example, the app logger is used in the exception handling of the try/except
in the route below:

```python
@app.get('/regions/<code>')
def get_region(code):
    try:
        region = db.session.execute(db.select(Region).filter_by(NOC=code)).scalar_one()
        result = region_schema.dump(region)
        return result
    except exc.NoResultFound as e:
        app.logger.error(f'Region code {code} was not found. Error: {e}')
        abort(404, description="Region not found")
```

Then run the app: `flask --app paralympics run --debug`

Go to http://127.0.0.1:5000/region/ZZA

View the log result in the terminal:

```text
[2023-12-31 15:35:56,789] ERROR in routes: Region code ZZA was not found. Error: No row was found when one was required
127.0.0.1 - - [31/Dec/2023 15:35:56] "GET /regions/ZZA HTTP/1.1" 404 -
```

Consider logging events such as info in the startup in `create_app()`:

```python
def create_app():
    app = Flask(__name__)
    # app config omitted here
    app.logger.setLevel("INFO")

    db.init_app(app)

    app.logger.debug(f"Current Environment: {os.getenv('ENVIRONMENT')}")
    app.logger.debug(f"Using Database: {app.config.get('DATABASE')}")
    return app
```

Or actions taken by users, e.g. when they log in in the /login route:

```python
 if user.check_password(auth.get('password')):
    # Log when the user logged in
    app.logger.info(f"{user.email} logged in at {datetime.utcnow()}")
```

It is likely more useful to output the errors to a file.

To do this, you need to configure Logging before the app starts.

Add the following function in `paralympics\__init__.py`:

```text
def configure_logging(app):
    """ Configures Flask logging to a file.

    Logging level is set to DEBUG when testing which generates more detail.
    """
    logging.basicConfig(format='[%(asctime)s] %(levelname)s %(name)s: %(message)s')

    if app.config['TESTING']:
        logging.getLogger().setLevel(logging.DEBUG)
        handler = logging.FileHandler('paralympics_tests.log')  # Log to a file
    else:
        logging.getLogger().setLevel(logging.INFO)
        handler = logging.FileHandler('paralympics.log')  # Log to a file
    
    app.logger.addHandler(handler)
```

Then create the logger in the `create_app` e.g.

```python
def create_app(test_config=None):
    app = Flask('paralympics', instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='l-tirPCf1S44mWAGoWqWlA',
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, 'paralympics.sqlite'),
    )
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Configure logging 
    configure_logging(app)

    # Log events to the logger
    app.logger.debug(f"Using Database: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

    # ... code omitted ...
```

Try running the tests, and then run the app and check for the two log files `paralympics.log`
and `paralympics_test.log`.

## 2. Configure Flask to handle errors and respond in JSON format

The Flask documentation
for [handling application errors in Flask](https://flask.palletsprojects.com/en/2.3.x/errorhandling/) explains how to
add custom errors. Much of this relates to returning HTML error pages which is not what we want in a REST API. We
instead want to return JSON format messages in our REST API.

The Flask documentation gives examples for the following:

- Handle non-HTTP exceptions as 500 Server error in JSON format
- Return JSON instead of HTML for HTTP errors.
- Handle a specific HTTP error (404 in this case) with custom message for the app when Flask.abort() is called.

There are two approaches for how to define these in Flask:

1. Define the functions and use the `app.errorhandler()` decorator. You could then add them to `routes.py`.
2. Define the functions and in the Factory function, `create_app()`, register the error handlers.

Approach 1:

You can add the following the `routes.py`.

In the week 5 completed example they are in `error_handlers.py` instead to keep the routes code shorter. To
ensure the app can find them, I updated `create_app()` to import them in the app.context() where the routes are
imported.

```python
from flask import json, current_app as app, jsonify
from werkzeug.exceptions import HTTPException


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle non-HTTP exceptions as 500 Server error in JSON format."""

    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e

    # now you're handling non-HTTP exceptions only
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": 500,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response


@app.errorhandler(404)
def resource_not_found(e):
    """Handle a specific HTTP error (404 in this case) with custom message for the app when Flask.abort() is called.
    """
    return jsonify(error=str(e)), 404
```

Approach 2: Define the error handling function and register it in the `create_app` factory function

The Flask documentation includes this in
the [Further Examples section](https://flask.palletsprojects.com/en/2.3.x/errorhandling/#further-examples).

Define the error handler and then register it in the create_app function.

There is an example of this in the week 5 completed code in the `paralympics\__init__.py` file:

```python
def handle_404_error(e):
    """ Error handler for 404.

        Used when abort() is called. THe custom message is provided by the 'description=' parameter in abort().
        Args:
            HTTP 404 error

        Returns:
            JSON response with the validation error message and the 404 status code
        """
    return jsonify(error=str(e)), 404


def create_app(test_config=None):
    app = Flask('paralympics', instance_relative_config=True)

    # ... code removed here for brevity ...

    # Register the custom 404 error handler that is defined in this python file
    app.register_error_handler(401, handle_404_error)

```

You could also specifically handle Marshmallow and SQLAlchemy errors, otherwise these will be handled by the generic '
Exception' handler. For example:

```python
@app.errorhandler(ValidationError)
def register_validation_error(error):
    """ Error handler for marshmallow schema validation errors.

    Args:
        error (ValidationError): Marshmallow error.

    Returns:
        HTTP response with the validation error message and the 400 status code
    """
    response = error.messages
    return response, 400
```

## 3. Use Python try / except in routes

This assumes you already implemented the error handling and set-up logging in the previous two steps!

Even if a statement or expression is syntactically correct, it may cause an error when an attempt is made to execute it.
Errors detected during execution are called `exceptions`. Source: Python

The Try Except block can include the following elements:

- The `try` block lets you test a block of code for errors.
- The `except` block lets you handle the error.
- The `else` block lets you execute code when there is no error.
- The `finally` block lets you execute code, regardless of the result of the try- and except blocks.

Source: w3schools

```python
def divide(x, y):
    try:
        # Floor Division : Gives only Fractional Part as Answer 
        result = x // y
    except ZeroDivisionError:
        print("Sorry ! You are dividing by zero ")
    else:
        print("Yeah ! Your answer is :", result)
    finally:
        # this block is always executed   
        # regardless of exception generation.  
        print('This is always executed')   
```

Source: https://www.geeksforgeeks.org/try-except-else-and-finally-in-python/

Consider the following code to delete a region:

```python
@app.delete('/regions/<noc_code>')
def delete_region(noc_code):
    """ Deletes the region with the given code.

    Args:
        param code (str): The 3-character NOC code of the region to delete
    Returns:
        JSON
    """
    region = db.session.execute(db.select(Region).filter_by(NOC=noc_code)).scalar_one()
    db.session.delete(region)
    db.session.commit()
    return {"message": f"Region {noc_code} deleted."}
```

This is OK if the Region code is found in the database, but if a code is passed that is not found in the database then
an error would occur.

A better solution would be to return an HTTP error in JSON syntax if the Region is not found. You could use the
Flask.abort(), Flask.make_response() or Flask.jsonify() methods to generate the error message in JSON.

You can also log the SQLAlchemy exception to the logger.

For example:

```python
@app.delete('/regions/<noc_code>')
def delete_region(noc_code):
    """ Deletes the region with the given code.

    Args:
        param code (str): The 3-character NOC code of the region to delete
    Returns:
        JSON If successful, return success message, other return 404 Not Found
    """
    try:
        region = db.session.execute(db.select(Region).filter_by(NOC=noc_code)).scalar_one()
        db.session.delete(region)
        db.session.commit()
        return {"message": f"Region {noc_code} deleted."}
    except exc.SQLAlchemyError as e:
        # Log the exception
        app.logger.error(f"A database error occurred: {str(e)}")
        # Return a 404 error to the user who made the request
        msg_content = f'Region {noc_code} not found'
        msg = {'message': msg_content}
        return make_response(msg, 404)
```

## Over to you

Error handling and logging has been added to the Region routes in the [completed code in week 5](https://github.com/nicholsons/comp0034-wk5-complete/blob/master/paralympics/routes.py).

Use try / except to handle potential exceptions for all the Event API routes.

## References

See Reading List on Moodle also.

- [Python 8.2 Exceptions](https://docs.python.org/3/tutorial/errors.html#exceptions)
- [W3Schools Try Except](https://www.w3schools.com/python/python_try_except.asp)
- [Handling application errors in Flask](https://flask.palletsprojects.com/en/3.0.x/errorhandling/)
- [Handling exceptions in Flask-SQLAlchemy](https://www.youtube.com/watch?v=P-Z1wXFW4Is)
- [Configure Logging for Flask SQLAlchemy Project](https://shzhangji.com/blog/2022/08/10/configure-logging-for-flask-sqlalchemy-project/)
