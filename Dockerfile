# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.12.2
FROM python:${PYTHON_VERSION}-slim as base

ARG UID=10001
ARG APP_USER=appuser
# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1
# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
RUN adduser \
    --disabled-password \
    --gecos "" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    --home "/${APP_USER}" \
    ${APP_USER}

# Install pdm as a package dependency manager 
# (rather than using pip, because package is pdm managed so i don't have a requirements.txt file at hand easily)
RUN python -m pip install pdm

# Go to working directory /app (now root . below is /app)
WORKDIR /app

# Copy the source code into the container.
COPY . .

# install venv, with dependancies (with gui optionnal dependancies, without dev dependancies)
RUN pdm install --group gui --prod


# Switch to the non-privileged user to run the application.
USER ${APP_USER}
# Expose the port that the application listens on.
EXPOSE 5000

# Run the application.
CMD pdm run foldermerge --gui --host "0.0.0.0"