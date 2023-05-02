#!/bin/bash

# Create the database for the playlist microservice.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE activities;
EOSQL

# Connect to the new database and create the tables.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "activities" <<-EOSQL
    CREATE TABLE IF NOT EXISTS activity_create_playlist (
      id SERIAL PRIMARY KEY,
      username VARCHAR(255) NOT NULL,
      playlist_id INTEGER NOT NULL,
      activity_timestamp TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS activity_add_song (
      id SERIAL PRIMARY KEY,
      username VARCHAR(255) NOT NULL,
      song_artist VARCHAR(255) NOT NULL,
      song_title VARCHAR(255) NOT NULL,
      playlist_id INTEGER NOT NULL,
      activity_timestamp TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS activity_make_friend (
      id SERIAL PRIMARY KEY,
      username VARCHAR(255) NOT NULL,
      username_friend VARCHAR(255) NOT NULL,
      activity_timestamp TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS activity_share_playlist (
      id SERIAL PRIMARY KEY,
      username VARCHAR(255) NOT NULL,
      username_friend VARCHAR(255) NOT NULL,
      playlist_id INTEGER NOT NULL,
      activity_timestamp TIMESTAMP DEFAULT NOW()
    );

EOSQL