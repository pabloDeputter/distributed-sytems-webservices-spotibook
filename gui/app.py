from flask import Flask, render_template, redirect, request, url_for
import requests

app = Flask(__name__)

# Microservice urls.
users_microservice_url = "http://users:5000"
friends_microservice_url = "http://friends:5000"
songs_microservice_url = "http://songs:5000"
playlists_microservice_url = "http://playlists:5000"
activities_microservice_url = "http://activities:5000"

# The Username & Password of the currently logged-in User
username = None
password = None

session_data = dict()


def save_to_session(key, value):
    session_data[key] = value


def load_from_session(key):
    return session_data.pop(key) if key in session_data else None  # Pop to ensure that it is only used once


def format_activity(act: dict) -> tuple:
    """
    Format a user activity dictionary into a tuple with a standardized format.

    :param act: A dictionary representing a user activity.

    :return: A tuple with three elements:
                - A string representing the timestamp of the activity.
                - A string representing a formatted message about the activity.
                - A string representing the username of the user performing the activity.
    """
    if act['activity_type'] == 'create_playlist':
        return act['timestamp'], act['username'], f'{act["activity_type"]} | created playlist {act["playlist_id"]}'
    elif act['activity_type'] == 'add_song':
        return act['timestamp'], act['username'],\
            f'{act["activity_type"]} add song {act["song_artist"]} | added {act["song_title"]} to {act["playlist_id"]}'
    elif act['activity_type'] == 'make_friend':
        return act['timestamp'], act['username'], f'{act["activity_type"]} | {act["username"]} befriended {act["username_friend"]}'
    elif act['activity_type'] == 'share_playlist':
        return act['timestamp'], act['username'], \
            f'{act["activity_type"]} | {act["username"]} shared playlist {act["playlist_id"]} with {act["username_friend"]}'

@app.route("/")
def feed():
    # ================================
    # FEATURE 9 (feed)
    #
    # Get the feed of the last N activities of your friends.
    # ================================

    global username

    N = 10
    if username is not None:
        feed = []
        # Retrieve the N latest activities from friends and sort them in descending order.
        response = requests.get(f'{activities_microservice_url}/activities/{username}?n={N}&sort=desc')

        # Check if status code of response is 200.
        if response.status_code == 200:
            feed = [format_activity(activity) for activity in response.json()['activities']]
    else:
        feed = []

    return render_template('feed.html', username=username, password=password, feed=feed)


@app.route("/catalogue")
def catalogue():
    songs = requests.get("http://songs:5000/songs").json()

    return render_template('catalogue.html', username=username, password=password, songs=songs)


@app.route("/login")
def login_page():
    success = load_from_session('success')
    return render_template('login.html', username=username, password=password, success=success)


@app.route("/login", methods=['POST'])
def actual_login():
    req_username, req_password = request.form['username'], request.form['password']

    # ================================
    # FEATURE 2 (login)
    #
    # send the username and password to the microservice
    # microservice returns True if correct combination, False if otherwise.
    # Also pay attention to the status code returned by the microservice.
    # ================================

    # Send post request to Users microservice to login.
    response = requests.post(f"{users_microservice_url}/users/login",
                             json={"username": req_username, "password": req_password})
    # If status code is 200, login is successful.
    success = response.status_code == 200
    save_to_session('success', success)
    if success:
        global username, password

        username = req_username
        password = req_password

    return redirect('/login')


@app.route("/register")
def register_page():
    success = load_from_session('success')
    return render_template('register.html', username=username, password=password, success=success)


@app.route("/register", methods=['POST'])
def actual_register():
    req_username, req_password = request.form['username'], request.form['password']

    # ================================
    # FEATURE 1 (register)
    #
    # send the username and password to the microservice
    # microservice returns True if registration is succesful, False if otherwise.
    #
    # Registration is successful if a user with the same username doesn't exist yet.
    # ================================

    # Send post request to Users microservice to register a new user.
    response = requests.post(f"{users_microservice_url}/users/register",
                             json={"username": req_username, "password": req_password})
    # If status code is 201, registration is successful.
    success = response.status_code == 201
    save_to_session('success', success)

    if success:
        global username, password

        username = req_username
        password = req_password

    return redirect('/register')


@app.route("/friends")
def friends():
    success = load_from_session('success')

    global username

    # ================================
    # FEATURE 4
    #
    # Get a list of friends for the currently logged-in user
    # ================================

    friend_list = []
    if username is not None:
        # Send post request to Friends microservice to retrieve friends.
        response = requests.get(f"{friends_microservice_url}/friends/{username}")
        # If status code is 200, user exists, we can retrieve the friends.
        if response.status_code == 200:
            # Response is a list of dictionaries, so we retrieve the usernames.
            friend_list = [i['username'] for i in response.json()['friends']]

    return render_template('friends.html', username=username, password=password, success=success,
                           friend_list=friend_list)


@app.route("/add_friend", methods=['POST'])
def add_friend():
    # ==============================
    # FEATURE 3
    #
    # send the username of the current user and the username of the added friend to the microservice
    # microservice returns True if the friend request is successful (the friend exists & is not already friends), False if otherwise
    # ==============================

    global username
    req_username = request.form['username']

    # Send post request to Friends microservice to add a friend.
    response = requests.post(f"{friends_microservice_url}/friends/add",
                             json={"username": username, "username_friend": req_username})

    # If status code is 200, friend request is successful.
    success = response.status_code == 200
    save_to_session('success', success)

    return redirect('/friends')


@app.route('/playlists')
def playlists():
    global username

    my_playlists = []
    shared_with_me = []

    if username is not None:
        # ================================
        # FEATURE
        #
        # Get all playlists you created and all playlist that are shared with you. (list of id, title pairs)
        # ================================

        # Send get request to Playlists microservice to retrieve both own playlist and shared playlists.
        response_own = requests.get(f'{playlists_microservice_url}/playlists?username={username}').json()
        response_shared = requests.get(f'{playlists_microservice_url}/playlists/shared?username={username}').json()

        # Convert response from list of dict. to list of tuples.
        my_playlists = [(playlist['id'], playlist['name']) for playlist in response_own['playlists']]
        shared_with_me = [(playlist['id'], playlist['name']) for playlist in response_shared['playlists']]

    return render_template('playlists.html', username=username, password=password, my_playlists=my_playlists,
                           shared_with_me=shared_with_me)


@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    # ================================
    # FEATURE 5
    #
    # Create a playlist by sending the owner and the title to the microservice.
    # ================================
    global username
    title = request.form['title']
    # Send post request to Playlists microservice to create a playlist.
    response = requests.post(f'{playlists_microservice_url}/playlists',
                             json={'owner': username, 'name': title})
    # If status code is 201, playlist is created. (check documentation of endpoint to check what can go wrong)

    return redirect('/playlists')


@app.route('/playlists/<int:playlist_id>')
def a_playlist(playlist_id):
    # ================================
    # FEATURE 7
    #
    # List all songs within a playlist
    # ================================
    # Send post request to Playlists microservice to retrieve all songs within playlist.
    response = requests.get(f'{playlists_microservice_url}/playlists/{playlist_id}').json()
    songs = [(song['song_title'], song['song_artist']) for song in response['songs']]

    return render_template('a_playlist.html', username=username, password=password, songs=songs,
                           playlist_id=playlist_id)


@app.route('/add_song_to/<int:playlist_id>', methods=["POST"])
def add_song_to_playlist(playlist_id):
    # ================================
    # FEATURE 6
    #
    # Add a song (represented by a title & artist) to a playlist (represented by an id)
    # ================================
    title, artist = request.form['title'], request.form['artist']

    # Send post request to Playlists microservice to add a song to a playlist.
    response = requests.post(f'{playlists_microservice_url}/playlists/{playlist_id}',
                             json={'song_title': title, 'song_artist': artist, 'added_by': username})


    # If status code is 200, song is added to playlist successfully. (check documentation of endpoint to check what can go wrong)
    return redirect(f'/playlists/{playlist_id}')


@app.route('/invite_user_to/<int:playlist_id>', methods=["POST"])
def invite_user_to_playlist(playlist_id):
    # ================================
    # FEATURE 8
    #
    # Share a playlist (represented by an id) with a user.
    # ================================
    recipient = request.form['user']
    # Send post request to Playlists microservice to share a playlist with recipient.
    response = requests.post(f'{playlists_microservice_url}/playlists/{playlist_id}/shares',
                  json={'recipient': recipient})


    return redirect(f'/playlists/{playlist_id}')


@app.route("/logout")
def logout():
    global username, password

    username = None
    password = None
    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
