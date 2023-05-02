# Assignment 2 - MicroServices

#### s0205440 - Pablo Deputter

## MicroServices Decomposition

To create a well-structured microservice architecture for the Spotibook scenario, I broke the features down in several
microservices. Each microservice apart from the GUI has its own database and communication channel with other
microservices. Here is the proposed MicroServices decomposition:

* Songs Service (existed already)
* GUI Service (existed already)
* Users Service
* Friends Service
* Playlists Service
* Activities Service

Every microservice has its own database or persistence storage system. Each database is also created using a separate
Docker container. Each database is initialised using a `init.sh` script, which is executed when the Docker container is
created. The 'init.sh' script creates the database and the tables, and inserts some initial data into the database.
The 'init.sh' script is located in the `docker-entrypoint-initdb.d` folder of each persistence storage of each
microservice. I had some issues though with initialising the database of the Activities Service. This was done by using
the following command `chmod + x ./init.sh`. I also provided some mock data for the Users service for example.

The Dockerfiles of each microservice apart from GUI are based of a based Dockerfile `base` since they all used the same
image.

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

For every required feature I documentate the endpoint that is used to perform the feature. Every endpoint is already
documented in the codebase in the following style. I didn't get Swagger to work, so I just stayed with ordinary
docstrings for documentation. For example, the following code implements the endpoint to retrieve and create playlists.
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


## Register User

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

## Errors

If the request fails, an error message will be returned in the response body.

Example error response:

```json
{
  "message": "User already exists"
}
```


## Login User

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

## Errors

If the request fails, an error message will be returned in the response body.

Example error response:

```json
{
  "message": "Invalid username or password"
}
```


## Add Friend

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

## Errors

If the request fails, an error message will be returned in the response body.

Example error response:

```json
{
  "message": "User not found"
}
```


## Get User's Friends

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

## Errors

If the request fails, an error message will be returned in the response body.

Example error response:

```json
{
  "message": "User not found"
}
``` 