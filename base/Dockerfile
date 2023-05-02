# syntax=docker/dockerfile:1
# Base image.
FROM python:3.8-slim-buster

# Set working directory.
WORKDIR /app

# Copy requirements file and install dependencies.
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY app.py app.py

# Set environment variable for Flask debug mode.
ENV FLASK_DEBUG=1

# Set command to run the app.
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]

