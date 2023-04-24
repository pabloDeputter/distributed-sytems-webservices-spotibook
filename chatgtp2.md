To create a well-structured microservice architecture for Spotibook, we will break down the features into separate microservices. These microservices will have their databases and communication channels with other microservices. Here's the proposed decomposition:

1. User Service:
   - Features:
     - User registration (1)
     - User login (2)
   - Database:
     - User Database (storing user information, including username and password)
   - Communication:
     - Exposes RESTful API for other microservices to access user information.

2. Friend Service:
   - Features:
     - Add friends (3)
     - List friends (4)
   - Database:
     - Friend Database (storing friend relationships)
   - Communication:
     - Exposes RESTful API for other microservices to access friend relationships.
     - Consumes User Service API to validate user existence.

3. Playlist Service:
   - Features:
     - Create playlists (5)
     - Add songs to a playlist (6)
     - View songs in a playlist (7)
     - Share a playlist with another user (8)
   - Database:
     - Playlist Database (storing playlists, songs, and shared playlists)
   - Communication:
     - Exposes RESTful API for other microservices to access playlists and songs.
     - Consumes User Service API to validate user existence.
     - Consumes Friend Service API to validate friend relationships when sharing playlists.

4. Activity Feed Service:
   - Features:
     - Generate activity feed for a user, showing the last N activities of friends (9)
   - Database:
     - Activity Feed Database (storing user activities)
   - Communication:
     - Exposes RESTful API for other microservices to access and add activities.
     - Consumes User Service, Friend Service, and Playlist Service APIs to generate activity feeds.

Decomposition Explanation:
- The User Service handles user registration and authentication, which are closely related tasks that involve user information. Grouping these features together ensures data consistency and security.
- The Friend Service is responsible for managing friend relationships between users, as these tasks are related to social networking features.
- The Playlist Service deals with playlist creation, song management, and sharing functionality, as these tasks are related to the core music streaming features of Spotibook.
- The Activity Feed Service is responsible for aggregating and presenting user activities, which is a separate concern that combines information from other microservices.

This decomposition groups related features together, allowing for easier maintainability and scalability. It also enables graceful failure, as each microservice can be deployed and scaled independently. Communication between microservices is handled through RESTful APIs, which promotes loose coupling and flexibility.