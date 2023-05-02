#!/bin/bash

# Create the database for the friend microservice.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE friends;
EOSQL

# Connect to the new database and create the friends table.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "friends" <<-EOSQL
    CREATE TABLE IF NOT EXISTS friends (
      id SERIAL PRIMARY KEY,
      username VARCHAR(255) NOT NULL,
      username_friend VARCHAR(255) NOT NULL,
      CONSTRAINT unique_friend_relationship UNIQUE (username, username_friend)
    );
EOSQL