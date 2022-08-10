# pin minor version to prevent frequent packages rebuild
FROM python:3.10.5-slim

WORKDIR /app

# gcc is required by uwsgi
ARG BUILD_DEPS='gcc'

ADD pyproject.toml pyproject.toml
ADD poetry.lock poetry.lock

RUN apt-get update && apt-get install -y $BUILD_DEPS && \
    pip install poetry --no-cache-dir && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-ansi --no-interaction && \
    rm -rf ~/.cache/pypoetry && \
    apt-get remove --purge --assume-yes $BUILD_DEPS && \
    apt-get autoremove --assume-yes && \
    apt-get autoclean && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ADD . .

RUN mkdir /app/dictrainer/static && \
    mkdir /app/dictrainer/media && \
    mkdir /app/dictrainer/usermedia && \
    adduser --no-create-home --uid 1000 appuser --home /app && chown -R appuser: /app

USER appuser

ENV DOCKERIZED=1

EXPOSE 8000
