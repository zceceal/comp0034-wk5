# Adding authentication to a Flask REST API

## Introduction

Since a REST API is accessed from code or command line tools, then you need an authentication mechanism that does not
require HTML pages.

This activity therefore considers the JSON web token (JWT) approach (refer to the lecture for more details on this
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

## Update the User class (model)

In `models.py` update the existing user class to add functions to:

1. Hash the text password
2. Verify a text password against the stored hashed password

Rather than save the password as plain text you should hash it as a security measure.Hashing in Python is the process of
converting an input
into a fixed-length sequence of bytes, called a hash or message digest. The hash is generated using a mathematical
function that maps the input data to a fixed-size array of bytes. Salting can aslo be used prior to
hashing. Salting adds a random string of characters to the text password before it is hashed.

There are various packages that can be used to create handle hashing and salting such as `hashlib`, `bcrypt`, `passlib`
and others. In
this example we use functions from `werkzeug` which is a package installed with Flask by default. `werkzeug` provides
numerous utilities for creating a Flask application that runs on a WSGI server. Werkzeug provides much of the underlying
functionality that supports HTTP request and response handling, exceptions, URL routing etc. `werkzeug` security package
includes methods to generate and check a hash.

Add the following code to the User class in `models.py`. Note that you need to change the `password` attribute to use
the hashed password rather than the plain text.

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

Note: You could also create a Marshmallow UserSchema as you did for the other models and use it in the routes. I haven't
done so in the following example code.

## Create functions to encode and decode a token

You could add these to the User class as suggested in this tutorial; or add them to the `routes.py`. In the completed
example in week5-complete I added them to a separate file called `helpers.py` to avoid adding non-route code to
routes.py.

```python
import jwt
from datetime import datetime, timedelta
from flask import make_response, current_app as app


def encode_auth_token(user_id):
    """Generates the Auth Token.
    
    This is called in the login route when the user attempts to log in.

    :param: string user_id  The user id of the user logging in
    :return: token
    """
    try:
        # See https://pyjwt.readthedocs.io/en/latest/api.html for the parameters
        token = jwt.encode(
            # Sets the token to expire in 5 mins
            payload={
                "exp": datetime.utcnow() + timedelta(minutes=5),
                "iat": datetime.utcnow(),
                "sub": user_id,
            },
            # Flask app secret key, matches the key used in the decode() in the decorator
            key=app.config['SECRET_KEY'],
            # Matches the algorithm in the decode() in the decorator
            algorithm='HS256'
        )
        return token
    except Exception as e:
        return e


def decode_auth_token(auth_token):
    """
    Decodes the auth token.
    :param auth_token:
    :return: token payload
    """
    # Use PyJWT.decode(token, key, algorithms) to decode the token with the public key for the app
    # See https://pyjwt.readthedocs.io/en/latest/api.html
    try:
        payload = jwt.decode(auth_token, app.config.get("SECRET_KEY"), algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return make_response({'message': "Token expired. Please log in again."}, 401)
    except jwt.InvalidTokenError:
        return make_response({'message': "Invalid token. Please log in again."}, 401)
```

## Create a decorator

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

Add the following to a new file with a relevant name, e.g. `helpers.py`, or `routes.py` if you
prefer:

```python
from functools import wraps
from flask import request, make_response
from paralympics import db
from paralympics.models import User
from paralympics.helpers import decode_auth_token


def token_required(f):
    """Require valid jwt for a route

    Decorator to protect routes using jwt
    """

    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        # See if there is an Authorization section in the HTTP request headers
        if "Authorization" in request.headers:
            token = request.headers.get("Authorization")

        # If not, then return a 401 error (missing or invalid authentication credentials)
        if not token:
            response = {"message": "Authentication Token missing"}
            return make_response(response, 401)
        # Check the token is valid using the decode_auth_token method you just created in the previous step
        token_payload = decode_auth_token(token)
        user_id = token_payload["sub"]
        # Find the user in the database using their email address which is in the data of the decoded token
        current_user = db.session.execute(db.select(User).filter_by(id=user_id)).scalar_one_or_none()
        if not current_user:
            response = {"message": "Invalid or missing token."}
            return make_response(response, 401)
        return f(*args, **kwargs)

    return decorator
```

You have now created the decorator that can decode the token and handle errors if the token is missing or invalid.

The next steps are to:

- create the token when the user successfully logs in with
- use the decorator to protect routes in the REST API

## Create the token in a login route

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
    If the user is not found in the database, or the password is incorrect, return 401 error
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

    # If the user is not found, or the password is incorrect, return 401 error
    if not user or not user.check_password(auth.get('password')):
        msg = {'message': 'Incorrect email or password.'}
        return make_response(msg, 401)

    # If all OK then create the token
    token = encode_auth_token(user.id)

    # Return the token and the user_id of the logged in user
    return make_response(jsonify({"user_id": user.id, "token": token}), 201)

```

## Secure routes using the `@token_required` decorator

Add `@token_required` to one or more routes. For example, users must be registered and logged in before they are allowed
to 'update' a Region.

Partial code shown below so that you can see the additional import `from paralympics.utilities import token_required`
that is required, and where to place the `@token_required` decorator. Note that the order of the decorators matters.

```python
from paralympics.helpers import token_required


@app.patch("/regions/<noc_code>")
@token_required
def region_update(noc_code):
# Code removed
```

## Tests for the authentication

For convenience, I added some additional fixtures to `conftest.py` in the completed example. These are currently
in `test_auth.py` to avoid confusion for students looking at this repo only for the results of last week's testing
activities.

The fixtures are:

- `new_user` which adds a User to the database
- `random_user_json` which generates a random email and password in JSON format so that the route to create new users
  can be tested repeatedly
- `login` to generate a token for a logged in user

Open the `test_auth.py` and you will see a few tests have been added that test the login and register routes, and also
test a route that is protected by login.

You could add a wider range of tests to these, e.g.

- Missing email or password on register
- Missing email or password on login
- Change the token expiry to less than a minute then try a route that requires authentication after the token expires.
  You would need to login and then add a wait to your test code that is longer than the token validity to before trying
  to access the protected route.
- Invalid email address format on register (you will need to update the User to validate the email address format)

Before you can run the auth_tests you will need to add the `@token_required` to the PATCH route for regions:

```python
from paralympics.helpers import token_required


@app.patch("/regions/<noc_code>")
@token_required
def region_update(noc_code):
```

## References

Also refer to the Reading List.

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
- investigate multi-factor authentication (possibly too much effort as you'd need to handle emails or some other
  authentication mechanism).
