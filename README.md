<div>
  <p align="center">
    <img src="docs/images/logo.png" height="100">
  </p>
  <h1 align="center"><strong>Pythogen</strong></h1>
</div>

Generator of python HTTP-clients from OpenApi specification based on `httpx` and `pydantic`.

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

## Development
- Activate environment
    ```shell
    rm -rf venv || true
    python3.9 -m venv venv
    source venv/bin/activate
    make requirements
    ```
- Make changes
- Execute `make clients-for-tests`
- Run tests `make tests-in-docker`
