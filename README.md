# Extras

_COMP0034 2023-24 Week 5 coding activities_

Neither of these are mandatory for the coursework baseline.

Effective and consistent error handling is a criterion in the code aspect at the higher grades.

Some students included authentication in their requirements and may therefore wish to implement this. This would
increase the challenge of the solution.

## 1. Preparation and introduction

This assumes you have already forked the coursework repository and cloned the resulting repository to your IDE.

1. Create and activate a virtual environment
2. Install the requirements `pip install -r requirements.txt`
3. Run the app `flask --app paralympics run --debug`
4. Open a browser and go to http://127.0.0.1:5000/regions (there is no longer a home page)
5. Stop the app using `CTRL+C`
6. Check that you have an instance folder containing `paralympics.sqlite`

## 2. Handling errors / exceptions

Last week there were some tests that failed as error handling had not yet been added to the app.

In a REST API, you want the results of any HTTP request to return JSON (or other format) as that is what the users will
be expecting in their application code. This activity therefore focuses on handling errors and returning any messages in
JSON format. There are tutorials for Flask that focus on HTML pages returned for errors, we will consider these in the
second part of the course, but not for the REST API.

In this activity you will:

- learn how to configure Flask to handle errors
- add error handling to the database requests
- use the logger to track events while the server is being used (useful for debugging)

### Configure Flask to handle errors and respond in JSON format

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

Approach 2: Define the functions and register in the create_app

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

## Handle Marshamallow and SQLAlchemy errors

You could also specifically handle Marshmallow and SQLAlchemy errors, otherwise these will be handled by the generic '
Exception' handler.

## Use logging to track events in a running Flask app

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
    """ Configures Flask loggong to a file.

    Logging level is set to DEBUG when testing which generates more detail.
    """
    logging.basicConfig(format='[%(asctime)s] %(levelname)s %(name)s: %(message)s')

    if app.config['TESTING']:
        logging.getLogger().setLevel(logging.DEBUG)
        handler = logging.FileHandler('paralympics_tests.log')  # Log to a file
        app.logger.addHandler(handler)
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

## 3. Adding authentication and authorisation to a REST API

Since a REST API is accessed from code or command line tools, then you need an authentication mechanism that does not
require HTML pages.

This tutorial therefore considers the JSON web token (JWT) approach (refer to the lecture for more details on this
and other approaches).

JWT works as follows:

- User requests access (e.g. with username / password)
- Server validates credentials
- Server creates a JWT (token) and sends it to the client
- Client stores that token and sends it in all subsequent HTTP requests in the header (until it expires)
- Server verifies the token and responds with data

This activity implements single-factor authentication and assumes that users all have the same role. You will need to
read beyond this activity to implement authorisation based on different roles and/or multi-factor authentication.

There are many Python and Flask-specific packages available that are designed to make it easier to implement JSON web
tokens. You can use any. This activity uses a Python package, [PyJWT](https://pypi.org/project/PyJWT/)

Whichever package and approach you decide to use, the steps will broadly involve:

- A python User class with the username, email, password (or whichever details you plan to use). Implement hashing for
  the passwords, don't store as plain text.
- Functions that generate and verify a token.
- Authorisation endpoints (routes) that create a user account, login and logout.
- A decorator that can be used to protect routes by checking that a user is logged in and their token is valid.
- Add the decorator to the routes that require login.

### Update the User class (model)

In `models.py` update the existing user class to add functions to:

1. Hash the text password
2. Verify a text password against the stored hashed password

There are various algorithms that can be used to create a hash such as `hashlib`, `bcrypt` and others. In this example
we use functions from `werkzeug` which is a package installed with Flask by default. `werkzeug` provides numerous
utilities for creating a Flask application that runs on a WSGI server. Werkzeug provides much of the underlying
functionality that supports HTTP request and response handling, exceptions, URL routing etc. `werkzeug` security package
includes methods to generate and check a hash.

Add the following code to the User class in `models.py`. Note that you need to change the `password` attribute to use
the
hashed password rather than the plain text.

For this app, authentication will require the user to provide an email address and password only.

```python
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    email: Mapped[str] = mapped_column(db.String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String, unique=True, nullable=False)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
```

### Create a decorator

A Python decorator dynamically alters the functionality of a function, method or class and is used when you need to
extend the functionality of functions.
You have already used decorators. In pytest you used decorators for fixtures by adding `@pytest.fixture()` above the
functions; and in Flask itself for routes `@app.route()`

The following code creates a decorator that will allow you to check if a user is authorised to use any routes that has
the decorator applied to it.

The decorator below:

- Checks if there is a token in the Authorization field in the headers part of the request; if this is missing, it
  returns an authorization error.
- Checks if the token exists but is not valid; if it is not valid, you also return an authorization error.
- If the checks are passed, then the route function is called.

The code below uses the Flask
method [`make_response`](https://flask.palletsprojects.com/en/3.0.x/api/#flask.Flask.make_response) which can take a
dict that will be `jsonify`'d before being returned.

Add the following to a new file with a relevant name, e.g. `utilities.py`. You could add it to `routes.py` if you
prefer, though the file is going to get long.:

```python
from functools import wraps
import jwt
from flask import request, make_response
from flask import current_app as app
from paralympics import db
from paralympics.models import User


def token_required(f):
    """Require valid jwt for a route

    Decorator to protect routes using jwt
    """

    @wraps(f)
    def decorator(*args, **kwargs):
        token = None

        # See if there is an Authorization section in the HTTP request headers
        if 'Authorization' in request.headers:
            token = request.headers.get("Authorization")

        # If not, then return a 401 error (missing or invalid authentication credentials)
        if not token:
            response = {"message": "Authentication Token missing"}
            return make_response(response, 401)
        # Check the token is valid and find the user in the database using their email address
        try:
            # Use PyJWT.decode(token, key, algorithms) to decode the token with the public key for the app
            # See https://pyjwt.readthedocs.io/en/latest/api.html
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            # Find the user in the database using their email address which is in the data of the decoded token
            current_user = db.session.execute(
                db.select(User).filter_by(email=data.get("email"))
            ).scalar_one_or_none()
        # If the email is not found, the token is likely invalid so return 401 error
        except:
            response = {"message": "Token invalid"}
            return make_response(response, 401)

        # If successful, return the user information attached to the token
        return f(current_user, *args, **kwargs)

    return decorator
```

You have now created the decorator that can decode the token and handle errors if the token is missing or invalid.

The next steps are to:

- Create the token
- Use the decorator to protect routes in the REST API

### Create the token in a login route

You will need to create at least two routes: one to create a new user account, and the second to handle login.

The comments in the code explain what the code does.

Add the routes to the `routes.py` file.

```python
from datetime import datetime, timedelta

import jwt
from flask import current_app as app, request, jsonify, make_response

from paralympics import db
from paralympics.models import User


@app.post("/register")
def register():
    """Register a new user for the REST API

    If successful, return 201 Created.
    If email already exists, return 409 Conflict (resource already exists).
    If any other error occurs, return 500 Server error
    """
    # Get the JSON data from the request
    post_data = request.get_json()
    # Check if user already exists, returns None if the user does not exist
    user = db.session.execute(
        db.select(User).filter_by(email=post_data.get("email"))
    ).scalar_one_or_none()
    if not user:
        try:
            # Create new User object
            user = User(email=post_data.get("email"))
            # Set the hashed password
            user.set_password(password=post_data.get("password"))
            # Add user to the database
            db.session.add(user)
            db.session.commit()
            # Return success message
            response = {
                "message": "Successfully registered.",
            }
            return make_response(jsonify(response)), 201
        except Exception as err:
            response = {
                "message": "An error occurred. Please try again.",
            }
            return make_response(jsonify(response)), 500
    else:
        response = {
            "message": "User already exists. Please Log in.",
        }
        return make_response(jsonify(response)), 409


@app.post('/login')
def login():
    """Logins in the User and generates a token
    
    If the email and password are not present in the HTTP request, return 401 error
    If the user is not found in the database, return 401 error
    If the password does not math the hashed password, return 403 error
    If the token is not generated or any other error occurs, return 500 Server error
    If the user is logged in and the token is generated, return the token and 201 Success
    """
    auth = request.get_json()
    # Check the email and password are present, if not return a 401 error
    if not auth or not auth.get('email') or not auth.get('password'):
        msg = {'message': 'Missing email or password'}
        return make_response(msg, 401)
    # Find the user in the database
    user = db.session.execute(
        db.select(User).filter_by(email=auth.get("email"))
    ).scalar_one_or_none()
    # If the user is not found, return 401 error
    if not user:
        msg = {'message': 'No account for that email address. Please register.'}
        return make_response(msg, 401)
    # Check if the password matches the hashed password using the check_password function you added to User in models.py
    if user.check_password(auth.get('password')):
        # The user is now verified so create the token
        # See https://pyjwt.readthedocs.io/en/latest/api.html for the parameters
        token = jwt.encode(
            # Sets the token to expire in 5 mins
            payload={
                "exp": datetime.utcnow() + timedelta(minutes=5),
                "iat": datetime.utcnow(),
                "sub": user.id,
            },
            # Flask app secret key, matches the key used in the decode() in the decorator
            key=app.config['SECRET_KEY'],
            # The id field from the User in models
            headers={'user_id': user.id},
            # Matches the algorithm in the decode() in the decorator
            algorithm='HS256'
        )
        return make_response(jsonify({'token': token}), 201)
    # If the password does not math the hashed password, return 403 error
    msg = {'message': 'Incorrect password.'}
    return make_response(msg, 403)
```

### Secure routes using the `@token_required` decorator

Add `@token_required` to one or more routes. For example, users must be registered and logged in before they are allowed
to 'update' a Region.

Partial code shown below so that you can see the additional import `from paralympics.utilities import token_required`
that is required, and where to place the `@token_required` decorator.

```python
from paralympics.utilities import token_required


@app.patch("/regions/<noc_code>")
@token_required
def region_update(noc_code):
# Code removed
```

### Tests for the authentication

For convenience, I added some additional fixtures to `conftest.py`:

- `new_user` which adds a User to the database so they can be used to test routes requiring login
- `random_user_json` which generates a random email and password in JSON format so that the route to create new users
  can be tested repeatedly
- `login_token`

Open the `test_auth.py` and you will see a few tests have been added that test the login and register routes, and also
test a route that is protected by login.

You could add a wider range of tests to these, e.g.

- Missing email or password on register
- Missing email or password on login
- Change the token expiry to less than a minute then try a route that requires authentication after the token expires.
  You would need to login and then add a wait to your test code that is longer than the token validity to before trying
  to access the protected route.
- Invalid email address format on register (you will need to update the User to validate the email address format)

## References

There are also links in the Reading List.

- [Handling application errors in Flask](https://flask.palletsprojects.com/en/2.3.x/errorhandling/)
- [Handling exceptions in Flask-SQLAlchemy](https://www.youtube.com/watch?v=P-Z1wXFW4Is )
- [Using authentication decorators in Flask (13 min read)](https://circleci.com/blog/authentication-decorators-flask/)

## Going further in the coursework

For the coursework you could consider:

- investigate Flask or other packages to implement jwt such as Miguel Grinberg's Flask-HTTPAuth package:

    - [API Authentication with Tokens](https://blog.miguelgrinberg.com/post/api-authentication-with-tokens)
    - [API chapter of his Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xxiii-application-programming-interfaces-apis).

- investigate Flask Blueprints and create the authorisation as a Blueprint. This would make it easier to re-use the
  authorisation in another app (for example in coursework 2). This is a more sophisticated way to structure Flask rather
  than more sophisticated authentication.
- investigate extending the authorisation process to allow for different roles (e.g. user, administrator).
- investigate multi-factor authentication (possibly too much work as you'd need to handle emails or some other
  authentication mechanism).
