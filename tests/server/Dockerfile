FROM python:3.9-slim

WORKDIR /opt/test_server
COPY requirements.txt .
RUN apt-get update && apt-get install -qq \
    gcc \
    libpq-dev
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt
COPY server.py .
