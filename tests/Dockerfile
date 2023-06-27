FROM python:3.10-slim

WORKDIR /opt/tests
COPY requirements.txt .
RUN apt-get update && apt-get install -qq \
    gcc \
    libpq-dev \
    git
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt
COPY clients ./clients
COPY main.py .
