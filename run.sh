#!/bin/bash

chmod +x ./activities_persistence/init.sh
chmod +x ./friends_persistence/init.sh
chmod +x ./playlists_persistence/init.sh
chmod +x ./songs_persistence/init.sh
chmod +x ./users_persistence/init.sh
# Start the GUI microservice since this depends on all the other microservices.
docker-compose up GUI --build

