from flask import Flask, jsonify
from flask import request as flask_request
from flask_restful import Resource, Api, reqparse

import requests
import psycopg2

app = Flask('playlists')
api = Api(app)

# Microservice URLs.
users_microservice_url = "http://users:5000"
songs_microservice_url = "http://songs:5000"
activities_microservice_url = "http://activities:5000"

conn = None

while conn is None:
    try:
        conn = psycopg2.connect(dbname="playlists", user="postgres", password="postgres", host="playlists_persistence")
        print("DB connection succesful")
    except psycopg2.OperationalError:
        import time

        time.sleep(1)
        print("Retrying DB connection")


def playlist_exists(playlist_id: int):
    """
    Checks if a playlist exists in the database.

    :param playlist_id: id of the playlist to check.
    :return: True if the playlist exists, False otherwise.
    """
    # Check if playlist exists.
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM playlists WHERE id=%s", (playlist_id,))
    return bool(cursor.fetchone())


def song_exists(title: str, artist: str):
    """
    Checks if a song exists in the Songs microservice.

    :param title: title of the song to check.
    :param artist: artist of the song to check.
    :return: True if the song exists, False otherwise.
    """
    response = requests.get(f'{songs_microservice_url}/songs/exist?title={title}&artist={artist}')
    return response.status_code == 200 and response.json()


class Playlists(Resource):
    """
    Resource for retrieving playlists and creating new playlists.

    GET /playlists?username=<username>
    Retrieves all playlists owned by the specified username.

    Response:
    - 200 OK: The playlists were retrieved successfully.

    POST /playlists
    Creates a new playlist with the specified name and owner.

    Request data:
    - name: The name of the new playlist.
    - owner: The username of the owner of the playlist.

    Response:
    - 201 Created: The playlist was created successfully.
    - 400 Bad Request: The playlist name already exists for the specified owner.
    - 404 Not Found: The owner could not be found in the database.
    """

    def get(self):
        # Retrieve playlists owned by the specified username (if provided).
        username = flask_request.args.get('username')
        cursor = conn.cursor()
        if username:
            cursor.execute("SELECT * FROM playlists WHERE owner = %s;", (username,))
        else:
            cursor.execute("SELECT * FROM playlists;")
        # Reformat the results.
        playlists = [{
            'id': row[0],
            'name': row[1],
            'owner': row[2],
            'created_at': row[3].strftime('%Y-%m-%d %H:%M:%S')  # Convert datetime to string.
        } for row in cursor.fetchall()]
        return {'playlists': playlists}, 200

    def post(self):
        # Parse the request data.
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('owner', type=str, required=True)
        args = parser.parse_args()

        # Check if the owner exists.
        response = requests.get(f'{users_microservice_url}/users/exists?username={args["owner"]}')
        # If the owner doesn't exist, we return a 404 Not Found.
        if not response.json()['exists']:
            return {'message': 'Owner not found'}, 404

        # Check if the playlist name already exists for the owner.
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id \
            FROM playlists \
            WHERE name = %s AND owner = %s;",
            (args['name'], args['owner']))
        # If the playlists name already exists for the specified owner, we return a 400 Bad Request.
        if cursor.fetchone():
            return {'message': 'Playlist name already exists for the specified owner'}, 400

        # Create the new playlist if everything is ok.
        cursor.execute(
            "INSERT INTO playlists (name, owner) \
            VALUES (%s, %s);", (args['name'], args['owner']))
        conn.commit()

        # Send post request to activities microservice to create new create_playlist activity.
        requests.post(f'{activities_microservice_url}/activities/create-playlist', json={
            'username': args['owner'],
            # Retrieve id of last created playlist.
            'playlist_id': cursor.lastrowid
        })

        return {'message': 'Playlist was created successfully'}, 201


class Playlist(Resource):
    """
    Resource for adding a song to a playlist and retrieving all songs in a playlist.

    GET /playlists/<playlist_id>
    Retrieve all songs from a playlist.

    Response:
    - 200 OK: The songs were retrieved successfully.
    - 404 Not Found: The playlist could not be found.

    POST /playlists/<playlist_id>
    Adds the specified song to the playlist.

    Request data:
    - song_artist: The artist of the song to be added.
    - song_title: The title of the song to be added.
    - added_by: The username of the user who added the song.

    Response:
    - 200 OK: The song was added to the playlist successfully.
    - 404 Not Found: The playlist or song to be added could not be found.
    """

    def get(self, playlist_id):
        # Return 404 Not Found.
        if not playlist_exists(playlist_id):
            return {'message': 'Playlist not found'}, 404

        cursor = conn.cursor()
        # Retrieve songs from playlist.
        cursor.execute("SELECT * FROM playlist_songs WHERE playlist_id=%s", (playlist_id,))
        # Reformat the results.
        songs = [{
            'id': row[0],
            'playlist_id': row[1],
            'song_artist': row[2],
            'song_title': row[3],
            'added_at': row[4].strftime('%Y-%m-%d %H:%M:%S')  # Convert datetime to string.
        } for row in cursor.fetchall()]
        return {'songs': songs}, 200

    def post(self, playlist_id):
        # Parse the request data.
        parser = reqparse.RequestParser()
        parser.add_argument('song_artist', type=str, required=True)
        parser.add_argument('song_title', type=str, required=True)
        parser.add_argument('added_by', type=str, required=True)
        args = parser.parse_args()

        # Return 404 Not Found if playlist doesn't exist.
        if not playlist_exists(playlist_id):
            return {'message': 'Playlist not found'}, 404

        # Return 404 Not Found if song to be added doesn't exist.
        if not song_exists(args['song_title'], args['song_artist']):
            return {'message': 'Song not found'}, 404

        cursor = conn.cursor()
        # Add the song to the playlist.
        cursor.execute(
            "INSERT INTO playlist_songs (playlist_id, song_artist, song_title) \
            VALUES (%s, %s, %s);", (playlist_id, args['song_artist'], args['song_title']))
        conn.commit()

        # Send request to Activities microservice to create new add_song activity.
        requests.post(f'{activities_microservice_url}/activities/add-song', json={
            'username': args['added_by'],
            'playlist_id': playlist_id,
            'song_artist': args['song_artist'],
            'song_title': args['song_title']
        })

        return {'message': 'Song added to playlist successfully'}, 200


class PlaylistShare(Resource):
    """
    Resource for sharing a playlist with another user.

    POST /playlists/<playlist_id>/shares
    Shares the specified playlist with the specified user.

    Request data:
    - recipient: The username of the user with whom the playlist is being shared.

    Response:
    - 200 OK: The playlist was shared successfully.
    - 400 Bad Request: The user tried to share the playlist with themselves.
    - 404 Not Found: The playlist or user could not be found in the database.
    - 409 Conflict: The playlist is already shared with the specified user.
    """

    def post(self, playlist_id):
        # Parse the request data.
        parser = reqparse.RequestParser()
        parser.add_argument('recipient', type=str, required=True)
        args = parser.parse_args()

        cursor = conn.cursor()
        # Check if the playlist exists.
        if not playlist_exists(playlist_id):
            return {'message': 'Playlist not found'}, 404

        # Check if the user being shared the playlist exists.
        response = requests.get(f'{users_microservice_url}/users/exists?username={args["recipient"]}')
        if not response.json()['exists']:
            return {'message': 'User not found'}, 404

        # Check if the user is sharing the playlist with themselves.
        cursor.execute("SELECT owner FROM playlists WHERE id=%s", (playlist_id,))
        owner = cursor.fetchone()[0]
        # Return 404 Bad Request.
        if owner == args['recipient']:
            return {'message': 'You cannot share the playlist with yourself'}, 400

        # Check if the playlist is already shared with the recipient.
        cursor.execute("SELECT * FROM playlist_shares WHERE playlist_id=%s AND username=%s",
                       (playlist_id, args['recipient']))
        if cursor.fetchone():
            return {'message': 'Playlist is already shared with the specified user'}, 409

        # Share the playlist with the user.
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO playlist_shares (playlist_id, username) \
            VALUES (%s, %s);", (playlist_id, args['recipient']))
        conn.commit()

        # Send request to Activities microservice to create new share_playlist activity.
        requests.post(f'{activities_microservice_url}/activities/share-playlist', json={
            'username': owner,
            'username_friend': args['recipient'],
            'playlist_id': playlist_id,
        })

        return {'message': 'Playlist shared successfully'}, 200


class SharedPlaylists(Resource):
    """
    Resource for retrieving all playlists shared with a user.

    GET /playlists/shared?username=<username>
    Retrieves all playlists shared with the specified username.

    Response:
    - 200 OK: The shared playlists were retrieved successfully.
    """
    def get(self):
        # Parse the request data.
        username = flask_request.args.get('username')
        cursor = conn.cursor()

        # Retrieve all playlists shared with the user.
        cursor.execute(
            "SELECT p.id, p.name, p.owner, p.created_at FROM playlists p \
            JOIN playlist_shares s ON p.id = s.playlist_id WHERE s.username = %s;", (username,))

        playlists = []
        # Reformat the results.
        playlists = [{
            'id': row[0],
            'name': row[1],
            'owner': row[2],
            'created_at': row[3].strftime('%Y-%m-%d %H:%M:%S')  # Convert datetime to string.
        } for row in cursor.fetchall()]
        return {'playlists': playlists}, 200


# Add the resources to the API.
api.add_resource(Playlists, '/playlists')
api.add_resource(Playlist, '/playlists/<int:playlist_id>')
api.add_resource(PlaylistShare, '/playlists/<int:playlist_id>/shares')
api.add_resource(SharedPlaylists, '/playlists/shared')
