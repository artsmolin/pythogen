<p align="center">
<img src="https://github.com/artsmolin/pythogen/raw/main/docs/img/logo.png" style="width: 100%; max-width: 500px" alt="pythogen">
<br />
Generator of python HTTP-clients from OpenApi specification based on <a href="https://github.com/projectdiscovery/httpx">httpx</a> and <a href="https://github.com/pydantic/pydantic">pydantic</a>.
</p>


<p align="center">
<a href="https://github.com/artsmolin/pythogen/actions" target="_blank">
    <img src="https://github.com/artsmolin/pythogen/actions/workflows/test.yml/badge.svg" alt="tests">
</a>
<a href="https://codecov.io/gh/artsmolin/pythogen" target="_blank">
    <img src="https://codecov.io/gh/artsmolin/pythogen/branch/main/graph/badge.svg?token=6JR6NB8Y9Z" alt="coverage">
</a>
<a href="https://pypi.org/project/pythogen/" target="_blank">
    <img src="https://img.shields.io/pypi/v/pythogen.svg?color=%2334D058" alt="pypi">
</a>
<a href="https://pypi.python.org/pypi/pythogen/" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/pythogen.svg?color=%2334D058" alt="python">
</a>
</p>

# Overview
## Installation
### with pip <small>recommended</small>
```shell
pip install pythogen
```
### with docker
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
Use the generated [client](/examples/petstore/client_async.py). Below is an example of using a client generated for [Petstore OpenAPI](/examples/petstore/openapi.yaml).
```python
from petstore.client_async import Client
from petstore.client_async import Pet
from petstore.client_async import EmptyBody
from petstore.client_async import FindPetsByStatusQueryParams

pets: list[Pet] | EmptyBody = await client.findPetsByStatus(
  query_params=FindPetsByStatusQueryParams(status="available"),
)
```

## Examples
- [Sync](/examples/petstore/client_sync.py) and [async](/examples/petstore/client_async.py) clients for [Petstore OpenAPI](/examples/petstore/openapi.yaml)
