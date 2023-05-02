## Assignment 2 - MicroServices

#### s0205440 - Pablo Deputter

## MicroServices Decomposition

To achieve a well-structured microservice architecture for the Spotibook scenario, the features were broken down into
several microservices. Apart from the GUI, each microservice has its own database and communication channel with other
microservices. The proposed Microservices decomposition is as follows:

* Songs Service (existed already)
* GUI Service (existed already)
* Users Service
* Friends Service
* Playlists Service
* Activities Service

Each microservice has its own database or persistence storage system. A separate Docker container is used to create each
database. Each database is initialised using an init.sh script, which is executed during the creation of the Docker
container. The init.sh script creates the database, tables, and inserts initial data into the database. This script is
located in the docker-entrypoint-initdb.d folder of each persistence storage of each microservice. However, the
Activities Service database initialisation faced some issues, which were resolved by executing the following command
chmod + x ./init.sh. Additionally, mock data was provided for the Users service.

To maintain consistency, the Dockerfiles of each microservice, apart from the GUI, are based on the base Dockerfile
since they all use the same image.

- GUI Service:
    - Communication:
        - Consumes Users Service API to validate user login and registration.
        - Consumes Friends Service API to retrieve friendship relationships of a user and add friends.
        - Consumes Songs Service API to retrieve songs.
        - Consumes Playlists Service API to retrieve playlists of a user, add songs, share playlist and creating
          playlists.
        - Consumes Activities Service API to create activities and retrieve activities of a user.

The GUI Service is responsible for the user interface of the application, providing a way for users to interact with the
system. It groups together features related to user authentication, friend management, playlist management, and activity
feed generation, as these are all key components of the application.

- Songs Service:
    - Database:
        - Songs Database (songs_persistence), storing of song information.
    - Communication:
        - Interacts with songs_persistence to retrieve/store song information.

The Songs Service is responsible for managing the storage and retrieval of song information, providing an interface for
other services to access the Songs Database. By separating this functionality into its own microservice, the system can
scale the storage and retrieval of song information independently of other services.

- Users Service:
    - Features:
        - User registration (1)
        - User login (2)
    - Database:
        - User Database (users_persistence), storing of username and password and possible other information.
    - Communication:
        - Interacts with users_persistence to retrieve/store user information.
        - Exposes RESTful API for other microservices to access user information, validate user existence and add users.

The Users Service is responsible for user management and authentication. By separating this functionality into its own
microservice, the system can enforce consistent and secure user authentication across all services.

- Friends Service:
    - Features:
        - Add friends (3)
        - List friends (4)
    - Database:
        - Friends Database (friends_persistence), storing of friendship relationships.
    - Communication:
        - Interacts with friends_persistence to retrieve/store friendship relationships.
        - Consumes Users Service API to validate user existence.
        - Exposes RESTful API for other microservices to access friend relationships and add friend relationships.

The Friends Service is responsible for managing friend relationships between users, as these tasks are related to social
networking features. By separating this functionality into its own microservice, the system can handle friend management
separately from other features, allowing for better scalability and modularity.

- Playlists Service:
    - Features:
        - Create playlists (5)
        - Add songs to a playlist (6)
        - View songs in a playlist (7)
        - Share a playlist with another user (8)
    - Database:
        - Playlists Database (playlists_persistence), storing of playlists, playlist songs and shared playlists.
    - Communication:
        - Interacts with playlists_perstistence to retrieve/store playlist information.
        - Consumes Users Service API to validate user existence.
        - Consumes Songs Service API to validate song existence.
        - Exposes RESTful API for other microservices to access playlists, playlist songs and shared playlists, create
          playlists, add songs to playlists, share playlists, ...

The Playlists Service is responsible for managing playlists, including the creation, adding of songs, and sharing of
playlists. By separating this functionality into its own microservice, the system can handle playlist management
separately from other features, allowing for better scalability and modularity.

- Activities Service:
    - Features:
        - Generate activity feed for a user, showing the last N activities of friends (9)
    - Database:
        - Activities Database (activities_persistence), storing of user activities.
    - Communication:
        - Interacts with activities_persistence to retrieve/store user activities.
        - Consumes Friends Service API to retrieve friendship relationships of a user.
        - Exposes RESTful API for other microservices to access user activities and create new activities.

The Activities Service is responsible for generating activity feeds for users. This is a separate concern that combines
information from other microservices. This can be seperated to centralize and manage activity data more efficiently.

This decomposition allows related functionalities to be
grouped together, which makes services more manageable and scalable. By breaking a monolithic system into smaller,
independent pieces, each microservice can be developed, deployed, and scaled independently. This improves fault
tolerance and makes graceful failure possible.

In addition to the benefits of manageability and fault tolerance, decomposition of features into microservices also
improves maintainability and scalability. Since each microservice is independent, changes can be made to one
microservice without affecting the others. This enables graceful failure, as each microservice can be deployed and
scaled independently.

Communication between microservices is typically handled through RESTful APIs. This promotes loose coupling and
flexibility, allowing each microservice to evolve and scale independently. By breaking down a monolithic system into
smaller, independent pieces, the microservice architecture enables teams to develop, deploy, and maintain software
systems with greater agility and ease.

## Features Documentation

To ensure clear and concise documentation of the required features, each feature has an associated endpoint, which is
documented using standard docstrings. Although Swagger was considered, ordinary docstrings were ultimately chosen for
documentation purposes.

For example, the following code provides an implementation for the creation and retrieval of playlists through an API
endpoint.

```python
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
        ...
        return {'playlists': playlists}, 200

    def post(self):
        ...
        if not response.json()['exists']:
            return {'message': 'Owner not found'}, 404
        ...
        if cursor.fetchone():
            return {'message': 'Playlist name already exists for the specified owner'}, 400
        ...
        return {'message': 'Playlist was created successfully'}, 201
```

If there are any endpoints that are missing from the README, their documentation can be found within the codebase. The
GUI and Songs services were not documented, as they either do not have any endpoints, were unchanged, or already have
adequate documentation.

## Users Service

### Register User

### `POST /register`

Creates a new user account with the provided username and password.

#### Request

The request must include the following parameters:

- `username`: The username of the user to be created.
- `password`: The password of the user to be created.

Example:

```json
{
  "username": "example_user",
  "password": "example_password"
}
```

#### Response

The response will be one of the following:

- `201 Created`: The user account was created successfully.
- `400 Bad Request`: The user account could not be created due to a missing or invalid username or password.
- `409 Conflict`: The user account could not be created because a user with the provided username already exists.

Example response for a successful request:

```json
{
  "message": "User created successfully"
}
```

### Errors

If the request fails, an error message will be returned in the response body.

Example error response:

```json
{
  "message": "User already exists"
}
```

### Login User

### `POST /login`

Logs in a user with the provided username and password.

#### Request

The request must include the following parameters:

- `username`: The username of the user to be logged in.
- `password`: The password of the user to be logged in.

Example:

```json
{
  "username": "example_user",
  "password": "example_password"
}
```

#### Response

The response will be one of the following:

- `200 OK`: The user was logged in successfully.
- `401 Unauthorized`: The login attempt was rejected due to an invalid username or password.

Example response for a successful request:

```json
{
  "message": "User logged in successfully"
}
```

### Errors

If the request fails, an error message will be returned in the response body.

Example error response:

```json
{
  "message": "Invalid username or password"
}
```

## Friends service

### Add Friend

### `POST /add_friend`

Adds the specified friend to the user's friend list.

#### Request

The request must include the following parameters:

- `username`: The ID username the user adding the friend.
- `username_friend`: The username of the friend to be added.

Example:

```json
{
  "username": "example_user",
  "username_friend": "example_friend"
}
```

#### Response

The response will be one of the following:

- `200 OK`: The friend was added successfully.
- `400 Bad Request`: The user tried to add themselves as a friend.
- `404 Not Found`: The user requesting the friendship or friend could not be found in the database.
- `409 Conflict`: The friendship already exists.

Example response for a successful request:

```json
{
  "message": "Friend added successfully"
}
```

### Errors

If the request fails, an error message will be returned in the response body.

Example error response:

```json
{
  "message": "User not found"
}
```

### Get User's Friends

### `GET /friends/<username>`

Returns a list of all friends associated with the given username.

#### Request

The request must include the following parameter:

- `username`: The username of the user whose friends should be listed.

#### Response

The response will be one of the following:

- `200 OK`: A list of friends associated with the given username.
- `404 Not Found`: The user could not be found in the database.

Example response for a successful request:

```json
{
  "friends": [
    {
      "username": "example_friend1"
    },
    {
      "username": "example_friend2"
    }
  ]
}
```

### Errors

If the request fails, an error message will be returned in the response body.

Example error response:

```json
{
  "message": "User not found"
}
``` 

## Playlists

### Create and retrieve playlists

Resource for retrieving playlists and creating new playlists.

### `GET /playlists?username=<username>`

Retrieves all playlists owned by the specified username.

#### Request

The request may include the following parameter:

- `username` (optional): The username of the owner of the playlists to be retrieved.

#### Response

The response will be one of the following:

- `200 OK`: The playlists were retrieved successfully.

Example response for a successful request:

```json
{
  "playlists": [
    {
      "id": 1,
      "name": "My Playlist",
      "owner": "my_username",
      "created_at": "2022-01-01 12:00:00"
    },
    {
      "id": 2,
      "name": "Another Playlist",
      "owner": "my_username",
      "created_at": "2022-01-02 12:00:00"
    }
  ]
}
```

### `POST /playlists`

Creates a new playlist with the specified name and owner.

#### Request

The request must include the following data:

- `name`: The name of the new playlist.
- `owner`: The username of the owner of the playlist.

#### Response

The response will be one of the following:

- `201 Created`: The playlist was created successfully.
- `400 Bad Request`: The playlist name already exists for the specified owner.
- `404 Not Found`: The owner could not be found in the database.

Example response for a successful request:

```json
{
  "message": "Playlist was created successfully"
}
```

### Add songs to a playlist and retrieve all songs in a playlist

Resource for adding a song to a playlist and retrieving all songs in a playlist.

### `GET /playlists/<playlist_id>`

Retrieve all songs from a playlist.

#### Request

The request must include the following parameter:

- `playlist_id`: The ID of the playlist to retrieve.

#### Response

The response will be one of the following:

- `200 OK`: The songs were retrieved successfully.
- `404 Not Found`: The playlist could not be found.

Example response for a successful request:

```json
{
  "songs": [
    {
      "id": 1,
      "playlist_id": 1,
      "song_artist": "Artist1",
      "song_title": "Song1",
      "added_at": "2022-01-01 12:00:00"
    },
    {
      "id": 2,
      "playlist_id": 1,
      "song_artist": "Artist2",
      "song_title": "Song2",
      "added_at": "2022-01-01 12:01:00"
    }
  ]
}
```

### `POST /playlists/<playlist_id>`

Adds the specified song to the playlist.

#### Request

The request must include the following data:

- `song_artist`: The artist of the song to be added.
- `song_title`: The title of the song to be added.
- `playlist_id`: The ID of the playlist to which the song should be added.

#### Response

The response will be one of the following:

- `200 OK`: The song was added to the playlist successfully.
- `404 Not Found`: The playlist or song to be added could not be found.

Example response for a successful request:

```json
{
  "message": "Song added to playlist successfully"
}
```

### Share playlist

Resource for sharing a playlist with another user.

### `POST /playlists/<playlist_id>/shares`

Shares the specified playlist with the specified user.

#### Request

The request must include the following
data:

- `recipient`: The username of the user with whom the playlist is being shared.
- `playlist_id`: The ID of the playlist to be shared.

#### Response

The response will be one of the following:

- `200 OK`: The playlist was shared successfully.
- `400 Bad Request`: The user tried to share the playlist with themselves.
- `404 Not Found`: The playlist or user could not be found in the database.
- `409 Conflict`: The playlist is already shared with the specified user.

Example response for a successful request:

```json
{
  "message": "Playlist shared successfully"
}
```

### Retrieve shared playlists

Resource for retrieving all playlists shared with a user.

### `GET /playlists/shared?username=<username>`

Retrieves all playlists shared with the specified username.

#### Request

The request must include the following parameter:

- `username`: The username of the user for whom shared playlists should be retrieved.

#### Response

The response will be one of the following:

- `200 OK`: The shared playlists were retrieved successfully.

Example response for a successful request:

```json
{
  "playlists": [
    {
      "id": 1,
      "name": "Shared Playlist 1",
      "owner": "another_username",
      "created_at": "2022-01-01 12:00:00"
    },
    {
      "id": 2,
      "name": "Shared Playlist 2",
      "owner": "another_username",
      "created_at": "2022-01-02 12:00:00"
    }
  ]
}
```

### Error Responses

If the request fails, an error message will be returned in the response body.

Example error response:

```json
{
  "message": "Playlist not found"
}
```

## Activities Service

### Retrieve Activities

### `GET /activities`

Retrieves the last N activities, sorted by time.

#### Request

The request may include the following query parameters:

- `n` (optional): The number of activities to retrieve, default is 10.
- `sort` (optional): The sort order (either 'asc' or 'desc'), default is 'desc'.

#### Response

The response will be one of the following:

- `200 OK`: The activities were retrieved successfully.

Example response for a successful request:

```json
{
  "activities": [
    {
      "activity_type": "add_song",
      "username": "example_user",
      "username_friend": null,
      "song_artist": "example_artist",
      "song_title": "example_song",
      "playlist_id": 123,
      "timestamp": "2023-05-01 15:30:00"
    },
    {
      "activity_type": "create_playlist",
      "username": "example_user",
      "username_friend": null,
      "song_artist": null,
      "song_title": null,
      "playlist_id": 456,
      "timestamp": "2023-04-30 12:00:00"
    }
  ]
}
```

### Retrieve Activities of User's Friends

### `GET /activities/<username>`

Retrieves the last N activities of the specified user's friends, sorted by time.

#### Request

The request must include the following query parameters:

- `username`: The username of the user whose friends' activities to retrieve.

The request may also include the following query parameters:

- `n` (optional): The number of activities to retrieve, default is 10.
- `sort` (optional): The sort order (either 'asc' or 'desc'), default is 'desc'.

#### Response

The response will be one of the following:

- `200 OK`: The activities were retrieved successfully.
- `404 Not Found`: The specified user does not exist.

Example response for a successful request:

```json
{
  "activities": [
    {
      "activity_type": "make_friend",
      "username": "example_user2",
      "username_friend": "example_user1",
      "song_artist": null,
      "song_title": null,
      "playlist_id": null,
      "timestamp": "2023-04-28 10:15:00"
    },
    {
      "activity_type": "share_playlist",
      "username": "example_user3",
      "username_friend": "example_user1",
      "song_artist": null,
      "song_title": null,
      "playlist_id": 789,
      "timestamp": "2023-04-26 20:45:00"
    }
  ]
}
```

### Create 'create_playlist' Activity

### `POST /activities/create-playlist`

Creates a new 'create_playlist' activity.

#### Request

The request must include the following data fields:

- `username`: The username who performed the activity.
- `playlist_id`: The ID of the playlist involved in the activity.

The request may also include the following optional data field:

- `timestamp`: The timestamp of the activity.

#### Response

The response will be one of the following:

- `201 Created`: The activity was created successfully.
- `400 Bad Request`: The request data was missing required fields or contained invalid values.

### Add Song Activity

### `POST /activities/add-song`

Creates a new 'add_song' activity.

#### Request Data

The request data must include the following parameters:

- `username`: The username who performed the activity.
- `song_artist`: The artist of the song that was added.
- `song_title`: The title of the song that was added.
- `playlist_id`: The ID of the playlist where the song was added.
- `timestamp` (optional): The timestamp of the activity.

#### Response

The response will be one of the following:

- `201 Created`: The activity was created successfully.
- `400 Bad Request`: The request data was missing required fields or contained invalid values.

Example response for a successful request:

```json
{
  "message": "Activity created successfully."
}
```

### Make Friend Activity

### `POST /activities/make-friend`

Creates a new 'make_friend' activity.

#### Request Data

The request data must include the following parameters:

- `username`: The username who performed the activity.
- `username_friend`: The username of the friend that was added.
- `timestamp` (optional): The timestamp of the activity.

#### Response

The response will be one of the following:

- `201 Created`: The activity was created successfully.
- `400 Bad Request`: The request data was missing required fields or contained invalid values.

Example response for a successful request:

```json
{
  "message": "Activity created successfully."
}
```

### Share Playlist Activity

### `POST /activities/share-playlist`

Creates a new 'share_playlist' activity.

#### Request Data

The request data must include the following parameters:

- `username`: The username who performed the activity.
- `username_friend`: The username of the friend those playlist was shared with.
- `playlist_id`: The ID of the playlist involved in the activity.
- `timestamp` (optional): The timestamp of the activity.

#### Response

The response will be one of the following:

- `201 Created`: The activity was created successfully.
- `400 Bad Request`: The request data was missing required fields or contained invalid values.

Example response for a successful request:

```json
{
  "message": "Activity created successfully."
}
```