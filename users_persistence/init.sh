#!/bin/bash

# Create the database for the user microservice.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE users;
EOSQL

# Connect to the new database and create the users table.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "users" <<-EOSQL
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL
    );
    COPY users (username, password)
    FROM '/docker-entrypoint-initdb.d/mock_users.csv'
    DELIMITER ','
    CSV HEADER;
EOSQL