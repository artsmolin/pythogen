<h2 align="center">Awesome python HTTP-clients from  OpenAPI</h2>

[![test](https://github.com/artsmolin/pythogen/actions/workflows/test.yml/badge.svg)](https://github.com/artsmolin/pythogen/actions)
[![lint](https://github.com/artsmolin/pythogen/actions/workflows/lint.yml/badge.svg)](https://github.com/artsmolin/pythogen/actions)
[![coverage](https://codecov.io/gh/artsmolin/pythogen/branch/main/graph/badge.svg?token=6JR6NB8Y9Z)](https://codecov.io/gh/artsmolin/pythogen)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
![downloads](https://img.shields.io/pypi/dm/pythogen)
[![python](https://img.shields.io/pypi/pyversions/pythogen.svg)](https://pypi.python.org/pypi/pythogen/)
[![pypi](https://img.shields.io/pypi/v/pythogen.svg)](https://pypi.org/project/pythogen/)
[![license](https://img.shields.io/github/license/artsmolin/pythogen.svg)](https://github.com/artsmolin/pythogen/blob/master/LICENSE)

---

Generator of python HTTP-clients from OpenApi specification based on <i>httpx</i> and <i>pydantic</i>

## Documentation
Check documentation to see more details about the features. All documentation is in the "docs" directory and online at [artsmolin.github.io/pythogen](https://artsmolin.github.io/pythogen)

## Examples
- [Sync](/examples/petstore/client_sync.py) and [async](/examples/petstore/client_async.py) clients for [Petstore OpenAPI](/examples/petstore/openapi.yaml)

## Installation
You can install the library
```shell
pip install pythogen
```
or use Docker
```shell
docker pull artsmolin/pythogen
```

## Generation
- `path/to/input` — path to the directory with openapi.yaml;
- `path/to/output` — the path to the directory where the generated client will be saved;

Generate a client using the installed library
```shell
pythogen path/to/input/openapi.yaml path/to/output/client.py
```

or via Docker
```shell
docker run \
-v ./path/to/input:/opt/path/to/input \
-v ./path/to/output:/opt/path/to/output \
artsmolin/pythogen \
path/to/input/openapi.yaml \
path/to/output/client.py
```

## Usage
```python
from petstore.client_async import Client
from petstore.client_async import Pet
from petstore.client_async import EmptyBody
from petstore.client_async import FindPetsByStatusQueryParams

client = Client(base_url="http://your.base.url")
pets: list[Pet] | EmptyBody = await client.findPetsByStatus(
  query_params=FindPetsByStatusQueryParams(status="available"),
)
```
