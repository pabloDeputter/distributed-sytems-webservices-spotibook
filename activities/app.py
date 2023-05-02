from flask import Flask, jsonify
from flask import request as flask_request
from flask_restful import Resource, Api, reqparse

import requests
import datetime
import psycopg2

app = Flask('activities')
api = Api(app)

# Microservice URLs.
friends_microservice_url = "http://friends:5000"

conn = None

while conn is None:
    try:
        conn = psycopg2.connect(dbname="activities", user="postgres", password="postgres",
                                host="activities_persistence")
        print("DB connection succesful")
    except psycopg2.OperationalError:
        import time

        time.sleep(1)
        print("Retrying DB connection")


class Activities(Resource):
    """
    Resource for retrieving the last N activities.

    GET /activities/?n=<n>&sort=<sort_order>
    Retrieves the last activities, sorted by time.

    Query parameters:
    - n: The number of activities to retrieve, default is 10.
    - sort: The sort order (either 'asc' or 'desc'), default is 'desc'.

    Response:
    - 200 OK: The activities were retrieved successfully.
    """

    def get(self):
        # Parse the request data.
        n = flask_request.args.get('n', type=int, default=10)
        sort = flask_request.args.get('sort', type=str, default='desc')

        # If the sort order is invalid set default to 'desc'.
        if sort not in ['asc', 'desc']:
            sort = 'desc'


        cursor = conn.cursor()
        # Retrieve the last N activities.
        cursor.execute("""
            WITH combined_activities AS (
                SELECT 'create_playlist' AS activity_type, username, NULL as username_friend, NULL AS song_artist, NULL AS song_title, playlist_id, activity_timestamp
                FROM activity_create_playlist
                UNION ALL
                SELECT 'add_song' AS activity_type, username, NULL as username_friend, song_artist, song_title, playlist_id, activity_timestamp
                FROM activity_add_song
                UNION ALL
                SELECT 'make_friend' AS activity_type, username, username_friend, NULL AS song_artist, NULL AS song_title, NULL AS playlist_id, activity_timestamp
                FROM activity_make_friend
                UNION ALL
                SELECT 'share_playlist' AS activity_type, username, username_friend, NULL AS song_artist, NULL AS song_title, playlist_id, activity_timestamp
                FROM activity_share_playlist)
            SELECT *
            FROM combined_activities
            ORDER BY activity_timestamp {sort_order}
            LIMIT {limit};""".format(sort_order=sort.upper(), limit=n))

        activities = [
            {
                'activity_type': row[0],
                'username': row[1],
                'username_friend': row[2],
                'song_artist': row[3],
                'song_title': row[4],
                'playlist_id': row[5],
                'timestamp': row[6].strftime('%Y-%m-%d %H:%M:%S'),
            }
            for row in cursor.fetchall()
        ]
        return {'activities': activities}, 200


class ActivitiesFriends(Resource):
    """
    Resource for retrieving the last N activities of a user's friends.

    GET /activities/<username>?n=<n>&sort=<sort_order>
    Retrieves the last N activities of the specified user's friends, sorted by time.

    Request data:
    - username: The username of the user whose friends' activities to retrieve.

    Query parameters:
    - n: The number of activities to retrieve, default is 10.
    - sort: The sort order (either 'asc' or 'desc'), default is 'desc'.

    Response:
    - 200 OK: The activities were retrieved successfully.
    - 404 Not Found: The specified user does not exist.
    """

    def get(self, username: str):
        # Parse the request data.
        n = flask_request.args.get('n', type=int, default=10)
        sort = flask_request.args.get('sort', type=str, default='desc')

        # If the sort order is invalid set default to 'desc'.
        if sort not in ['asc', 'desc']:
            sort = 'desc'

        # Retrieve friends of user. We don't check if the user exists since
        # the Friends microservice will do that before returning the friends.
        response = requests.get(f'{friends_microservice_url}/friends/{username}')
        if response.status_code == 404:
            return {'message': 'User does not exist.'}, 404
        else:
            friends = [friend['username'] for friend in response.json()['friends']]

        cursor = conn.cursor()
        # Retrieve the last N activities of the user's friends.
        # It doesn't matter if user A or user B added each other as friend, both are seen as an activity, by separate users.
        # The same goes for sharing playlists.
        cursor.execute("""
            WITH combined_activities AS (
                SELECT 'create_playlist' AS activity_type, username, NULL as username_friend, NULL AS song_artist, NULL AS song_title, playlist_id, activity_timestamp
                FROM activity_create_playlist
                UNION ALL
                SELECT 'add_song' AS activity_type, username, NULL as username_friend, song_artist, song_title, playlist_id, activity_timestamp
                FROM activity_add_song
                UNION ALL
                SELECT 'make_friend' AS activity_type, username, username_friend, NULL AS song_artist, NULL AS song_title, NULL AS playlist_id, activity_timestamp
                FROM activity_make_friend
                UNION ALL
                SELECT 'share_playlist' AS activity_type, username, username_friend, NULL AS song_artist, NULL AS song_title, playlist_id, activity_timestamp
                FROM activity_share_playlist)
            SELECT *
            FROM combined_activities
            WHERE username IN %s
            ORDER BY activity_timestamp {sort_order}
            LIMIT {limit};""".format(sort_order=sort.upper(), limit=n), (tuple(friends),))

        activities = [
            {
                'activity_type': row[0],
                'username': row[1],
                'username_friend': row[2],
                'song_artist': row[3],
                'song_title': row[4],
                'playlist_id': row[5],
                'timestamp': row[6].strftime('%Y-%m-%d %H:%M:%S'),
            }
            for row in cursor.fetchall()
        ]
        return {'activities': activities}, 200


class ActivityCreatePlaylist(Resource):
    """
    POST /activities/create-playlist
    Creates a new 'create_playlist' activity.

    Request data:
    - username: The username who performed the activity.
    - playlist_id: The ID of the playlist involved in the activity.
    - timestamp (optional): The timestamp of the activity.

    Response:
    - 201 Created: The activity was created successfully.
    - 400 Bad Request: The request data was missing required fields or contained invalid values.
    """

    def post(self):
        # Parse the request data.
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True)
        parser.add_argument('playlist_id', type=int, required=True)
        parser.add_argument('timestamp', type=str, required=False)
        args = parser.parse_args()

        # We don't check if the user or playlist exists since this is already done by the one who sends the request.
        cursor = conn.cursor()
        # Create the activity.
        cursor.execute("""
            INSERT INTO activity_create_playlist (username, playlist_id, activity_timestamp)
            VALUES (%s, %s, %s)""",
                       (args['username'], args['playlist_id'], args['timestamp'] or datetime.datetime.now()))
        conn.commit()

        return {'message': 'Activity created successfully.'}, 201


class ActivityAddSong(Resource):
    """
    POST /activities/add-song
    Creates a new 'add_song' activity.

    Request data:
    - username: The username who performed the activity.
    - song_artist: The artist of the song that was added.
    - song_title: The title of the song that was added.
    - playlist_id: The ID of the playlist where the song was added.
    - timestamp (optional): The timestamp of the activity.

    Response:
    - 201 Created: The activity was created successfully.
    - 400 Bad Request: The request data was missing required fields or contained invalid values.
    """

    def post(self):
        # Parse the request data.
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True)
        parser.add_argument('song_artist', type=str, required=True)
        parser.add_argument('song_title', type=str, required=True)
        parser.add_argument('playlist_id', type=int, required=True)
        parser.add_argument('timestamp', type=str, required=False)
        args = parser.parse_args()

        # We don't check if the user or song exists since this is already done by the one who sends the request.
        cursor = conn.cursor()
        # Create the activity.
        cursor.execute("""
            INSERT INTO activity_add_song (username, song_artist, song_title, playlist_id, activity_timestamp)
            VALUES (%s, %s, %s, %s, %s)""",
                       (args['username'], args['song_artist'], args['song_title'], args['playlist_id'],
                        args['timestamp'] or datetime.datetime.now()))
        conn.commit()

        return {'message': 'Activity created successfully.'}, 201


class ActivityMakeFriend(Resource):
    """
    POST /activities/make-friend
    Creates a new 'make_friend' activity.

    Request data:
    - username: The username who performed the activity.
    - username_friend: The username of the friend that was added.
    - timestamp (optional): The timestamp of the activity.

    Response:
    - 201 Created: The activity was created successfully.
    - 400 Bad Request: The request data was missing required fields or contained invalid values.
    """

    def post(self):
        # Parse the request data.
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True)
        parser.add_argument('username_friend', type=str, required=True)
        parser.add_argument('timestamp', type=str, required=False)
        args = parser.parse_args()

        # We don't check if the user or friend exists since this is already done by the one who sends the request.
        cursor = conn.cursor()
        # Create the activity.
        cursor.execute("""
            INSERT INTO activity_make_friend (username, username_friend, activity_timestamp)
            VALUES (%s, %s, %s)""",
                       (args['username'], args['username_friend'], args['timestamp'] or datetime.datetime.now()))
        conn.commit()

        return {'message': 'Activity created successfully.'}, 201


class ActivitySharePlaylist(Resource):
    """
    POST /activities/share-playlist
    Creates a new 'share_playlist' activity.

    Request data:
    - username: The username who performed the activity.
    - username_friend: The username of the friend those playlist was shared with.
    - playlist_id: The ID of the playlist involved in the activity.
    - timestamp (optional): The timestamp of the activity.

    Response:
    - 201 Created: The activity was created successfully.
    - 400 Bad Request: The request data was missing required fields or contained invalid values.
    """

    def post(self):
        # Parse the request data.
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True)
        parser.add_argument('username_friend', type=str, required=True)
        parser.add_argument('playlist_id', type=int, required=True)
        parser.add_argument('timestamp', type=str, required=False)
        args = parser.parse_args()

        # We don't check if the user, friend or playlist_id exists since this is already done by the one who sends the request.
        cursor = conn.cursor()
        # Create the activity.
        cursor.execute("""
            INSERT INTO activity_share_playlist (username, username_friend, playlist_id, activity_timestamp)
            VALUES (%s, %s, %s, %s)""",
                       (args['username'], args['username_friend'], args['playlist_id'],
                        args['timestamp'] or datetime.datetime.now()))
        conn.commit()

        return {'message': 'Activity created successfully.'}, 201


# Add the resources to the API.
api.add_resource(Activities, '/activities')
api.add_resource(ActivitiesFriends, '/activities/<username>')
# Resources for adding a new activity.
api.add_resource(ActivityCreatePlaylist, '/activities/create-playlist')
api.add_resource(ActivityAddSong, '/activities/add-song')
api.add_resource(ActivityMakeFriend, '/activities/make-friend')
api.add_resource(ActivitySharePlaylist, '/activities/share-playlist')
