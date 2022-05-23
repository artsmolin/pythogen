FROM python:3.9-slim-bullseye as builder
RUN apt update && apt-get install -y git gcc libpq-dev && rm -rf /var/lib/apt/lists/* /var/cache/apt/* /tmp/*
RUN pip install pip==21.2.4 poetry==1.1.8
COPY ./poetry.lock ./pyproject.toml ./
RUN poetry config virtualenvs.create false && poetry install

FROM python:3.9-slim-bullseye
RUN apt update && apt-get install -y git make gcc libpq-dev && rm -rf /var/lib/apt/lists/* /var/cache/apt/* /tmp/*
COPY --from=builder /usr/local /usr/local/
COPY ./pythogen                    /pythogen
COPY ./tests                       /tests
COPY ./Makefile                    /
COPY ./setup.cfg                   /
COPY ./.pre-commit-config.yaml     /
