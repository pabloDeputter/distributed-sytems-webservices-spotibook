from flask import Flask, jsonify
from flask import request as flask_request
from flask_restful import Resource, Api, reqparse

import psycopg2

app = Flask('users')
api = Api(app)

# Microservice URLs.
users_microservice_url = "http://users:5000"

conn = None

while conn is None:
    try:
        conn = psycopg2.connect(dbname="users", user="postgres", password="postgres", host="users_persistence")
        print("DB connection succesful")
    except psycopg2.OperationalError:
        import time

        time.sleep(1)
        print("Retrying DB connection")


def user_exists(username: str):
    """
    Checks if a user exists in the system.

    :param username: The username of the user to check.
    :return: True if the user exists, False otherwise.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
    return bool(cursor.fetchone()[0])


class User(Resource):
    """
    Resource for user information.

    GET /users/<username>
    Returns the user information for the specified user.

    Response:
    - 200 OK: The user information was returned successfully.
    - 404 Not Found: The specified user could not be found in the system.
    """

    def get(self, username: str):
        # Check if the user exists.
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if user := cursor.fetchone():
            return {
                'id': user[0],
                'username': user[1],
                'password': user[2]
            }, 200
        # Return a 404 Not Found error.
        return {'message': 'The specified user could not be found in the system.'}, 404


class Users(Resource):
    """
    Resource for retrieving all users.

    GET /users
    Returns a list of all users.

    Response:
    - 200 OK: The list of all users was returned successfully.
    """

    def get(self):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        return jsonify([
            {
                'id': user[0],
                'username': user[1],
                'password': user[2]
            } for user in users
        ])


class UserExists(Resource):
    """
    Resource for checking if a user exists.

    GET /users/exists?username=<username>
    Returns True if the specified user exists in the database, otherwise returns False.

    Response:
    - 200 OK: The existence of the specified user was returned successfully.
    - 400 Bad request: The username query parameter was missing.
    """

    def get(self):
        # Parse the query parameter.
        args = flask_request.args
        username = args.get('username')
        return (
            {'exists': user_exists(username)}, 200
            if username
            else ({'message': 'Missing query parameter: username'}, 400)
        )


class UserRegistration(Resource):
    """
    Resource for user registration.

    POST /register
    Creates a new user account with the provided username and password.

    Request data:
    - username: The username of the user to be created.
    - password: The password of the user to be created.

    Response:
    - 201 Created: The user account was created successfully.
    - 400 Bad Request: The user account could not be created due to a missing or invalid username or password.
    - 409 Conflict: The user account could not be created because a user with the provided username already exists.
    """

    def post(self):
        # Parse the request data.
        parser = reqparse.RequestParser()
        parser.add_argument('username', required=True)
        parser.add_argument('password', required=True)
        args = parser.parse_args()

        # Check if the user already exists.
        if user_exists(args['username']):
            return {'message': 'User already exists'}, 409

        # Create a new user.
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (args['username'], args['password']))
        conn.commit()
        return {'message': 'User created successfully'}, 201


class UserLogin(Resource):
    """
    Resource for user login.

    POST /login
    Logs in a user with the provided username and password.

    Request data:
    - username: The username of the user to be logged in.
    - password: The password of the user to be logged in.

    Response:
    - 200 OK: The user was logged in successfully.
    - 401 Unauthorized: The login attempt was rejected due to an invalid username or password.
    """

    def post(self):
        # Parse the request data.
        parser = reqparse.RequestParser()
        parser.add_argument('username', required=True)
        parser.add_argument('password', required=True)
        args = parser.parse_args()

        # Retrieve the user from the database.
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s",
                       (args['username'], args['password']))
        if user := cursor.fetchone():
            return {'message': 'User logged in successfully'}, 200
        else:
            return {'message': 'Invalid username or password'}, 401


# Add the resources to the API.
api.add_resource(Users, '/users')
api.add_resource(User, '/users/<username>')
api.add_resource(UserExists, '/users/exists')
api.add_resource(UserRegistration, '/users/register')
api.add_resource(UserLogin, '/users/login')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
