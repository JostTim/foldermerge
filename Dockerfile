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

WORKDIR /app
# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
RUN adduser \
    --disabled-password \
    --gecos "" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    ${APP_USER}
# RUN mkdir /home/$USER
# ENV HOME=/home/$USER
# RUN chown $USER: /home/$USER -R

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
# RUN --mount=type=cache,target=/root/.cache/pip \
    # --mount=type=bind,source=requirements.txt,target=requirements.txt \
RUN python -m pip install pdm

# Switch to the non-privileged user to run the application.

# Copy the source code into the container.
COPY . .
RUN pdm install --group gui --prod


# Switch to the non-privileged user to run the application.
USER ${APP_USER}
# Expose the port that the application listens on.
EXPOSE 5000

# ENV PYTHONPATH=/app/.venv/Scripts
# Run the application.

CMD pdm run foldermerge --gui --host "0.0.0.0"
# CMD pdm run gunicorn -w 1 'foldermerge:create_app()' --bind=0.0.0.0:5000
