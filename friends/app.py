from flask import Flask, jsonify
from flask import request as flask_request
from flask_restful import Resource, Api, reqparse

import requests
import psycopg2

app = Flask('friends')
api = Api(app)

# Microservice URLs.
users_microservice_url = "http://users:5000"

conn = None

while conn is None:
    try:
        conn = psycopg2.connect(dbname="friends", user="postgres", password="postgres", host="friends_persistence")
        print("DB connection succesful")
    except psycopg2.OperationalError:
        import time

        time.sleep(1)
        print("Retrying DB connection")


class AddFriend(Resource):
    """
    Resource for adding a friend.

    POST /add_friend
    Adds the specified friend to the user's friend list.

    Request data:
    - username: The ID username the user adding the friend.
    - username_friend: The username of the friend to be added.

    Response:
    - 200 OK: The friend was added successfully.
    - 400 Bad Request: The user tried to add themselves as a friend.
    - 404 Not Found: The user requesting the friendship or friend could not be found in the database.
    - 409 Conflict: The friendship already exists.
    """

    def post(self):
        # Parse the request data.
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True)
        parser.add_argument('username_friend', type=str, required=True)
        args = parser.parse_args()

        # Check if user friends themselves.
        if args['username'] == args['username_friend']:
            return {'message': 'You cannot add yourself as a friend'}, 400

        # Check if the user that requested the friendship exists.
        response = requests.get(f'{users_microservice_url}/users/exists?username={args["username"]}')
        # Check if friend exists.
        response_friend = requests.get(f'{users_microservice_url}/users/exists?username={args["username_friend"]}')

        cursor = conn.cursor()
        if not response.json()['exists'] or not response_friend.json()['exists']:
            return {'message': 'User or friend not found'}, 404
        # Check if the friend relationship already exists in db.
        cursor.execute(
            "INSERT INTO friends (username, username_friend) \
             SELECT %s, %s WHERE NOT EXISTS \
             (SELECT * FROM friends WHERE (username = %s AND username_friend = %s) OR (username = %s AND username_friend = %s));",
            (args['username'], args['username_friend'], args['username'], args['username_friend'],
             args['username_friend'], args['username']))
        conn.commit()

        if cursor.rowcount == 0:
            return {'message': 'Friendship already exists'}, 409
        return {'message': 'Friend added successfully'}, 200



class Friends(Resource):
    """
    Resource for listing a user's friends.

    GET /friends/<username>
    Returns a list of all friends associated with the given username.

    Request data:
    - username: The username of the user whose friends should be listed.

    Response:
    - 200 OK: A list of friends associated with the given username.
    - 404 Not Found: The user could not be found in the database.
    """

    def get(self, username: str):
        # Check if the user exists.
        response = requests.get(f'{users_microservice_url}/users/exists?username={username}')
        if not response.json()['exists']:
            return {'message': 'User not found'}, 404

        # List users friends.
        cursor = conn.cursor()
        # Retrieve the user's friends.
        cursor.execute(
            "SELECT username_friend \
            FROM friends \
            WHERE username = %s \
            UNION \
            SELECT username \
            FROM friends \
            WHERE username_friend = %s;",
            (username, username))

        # Reformat the results.
        friends = [{'username': row[0]} for row in cursor.fetchall()]
        return {'friends': friends}, 200


# Add the resources to the API.
api.add_resource(AddFriend, '/friends/add')
api.add_resource(Friends, '/friends/<username>')
