<div>
  <p align="center">
    <img src="docs/images/logo.png" height="100">
  </p>
  <h1 align="center"><strong>Pythogen</strong></h1>
</div>

Generator of python HTTP-clients from OpenApi specification based on `httpx` and `pydantic`.

[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


## Features
- [Discriminator](/docs/discriminator.md)
- Sync and async clients
- Tracing
- Metrics

## Installation
```shell
pip install pythogen
```

## Usage
Generate asynchronous client
```shell
pythogen path/to/input/openapi.yaml path/to/output/client.py
```
Generate synchronous client
```shell
pythogen path/to/input/openapi.yaml path/to/output/client.py --sync
```
Generate client as python-package
```shell
pythogen path/to/input/openapi.yaml path/to/package/output --package-version=0.0.1 --package-authors="Rick, Morty"
```

## Development
- Activate environment
    ```shell
    rm -rf venv || true
    python3.9 -m venv venv
    source venv/bin/activate
    make requirements
    ```
- Make changes
- Run `make test`
- Execute `make clients-for-tests && make test-clients`
