#!/bin/bash

# Create the database for the playlist microservice.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE playlists;
EOSQL

# Connect to the new database and create the tables.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "playlists" <<-EOSQL
    CREATE TABLE IF NOT EXISTS playlists (
      id SERIAL PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      owner VARCHAR(255) NOT NULL,
      created_at TIMESTAMP DEFAULT NOW(),
      CONSTRAINT unique_playlist_name_owner UNIQUE (name, owner)
    );

    CREATE TABLE IF NOT EXISTS playlist_songs (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER NOT NULL REFERENCES playlists(id),
    song_artist VARCHAR(255) NOT NULL,
    song_title VARCHAR(255) NOT NULL,
    added_at TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS playlist_shares (
      id SERIAL PRIMARY KEY,
      playlist_id INTEGER NOT NULL REFERENCES playlists(id),
      username VARCHAR(255) NOT NULL,
      shared_at TIMESTAMP DEFAULT NOW()
    );
EOSQL
