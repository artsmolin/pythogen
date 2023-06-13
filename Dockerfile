FROM python:3.11-slim-bullseye as builder
ENV POETRY_VERSION=1.3.1
ENV PIP_VERSION=22.3.1
RUN apt-get update && \
    apt-get install -y g++ && \
    pip install -U "pip==$PIP_VERSION" && \
    pip install --no-cache-dir "poetry==$POETRY_VERSION"
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

FROM python:3.11-slim-bullseye
COPY --from=builder /usr/local /usr/local/
COPY ./pythogen       /opt/pythogen
ENV PYTHONPATH "${PYTHONPATH}:/opt"
WORKDIR /opt
ENTRYPOINT ["python", "pythogen/entrypoint.py"]
