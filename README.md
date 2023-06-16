<div>
  <p align="center">
    <img src="docs/images/logo_long.png" height="auto" width="400px">
  </p>
  <br/>
</div>

Generator of python HTTP-clients from OpenApi specification based on [httpx](https://github.com/projectdiscovery/httpx) and [pydantic](https://github.com/pydantic/pydantic).

[![Build Status](https://github.com/artsmolin/pythogen/actions/workflows/main.yml/badge.svg)](https://github.com/artsmolin/pythogen/actions)
[![codecov](https://codecov.io/gh/artsmolin/pythogen/branch/main/graph/badge.svg?token=6JR6NB8Y9Z)](https://codecov.io/gh/artsmolin/pythogen)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![Python](https://img.shields.io/pypi/pyversions/pythogen.svg)](https://pypi.python.org/pypi/pythogen/)
[![pypi](https://img.shields.io/pypi/v/pythogen.svg)](https://pypi.org/project/pythogen/)

[![license](https://img.shields.io/github/license/artsmolin/pythogen.svg)](https://github.com/artsmolin/pythogen/blob/master/LICENSE)

---

<p align="center">
  <img src="docs/images/example.png">
</p>

## Features
- [Discriminator](/docs/discriminator.md)
- [Metrics](/docs/metrics.md)
- [Logs](/docs/logs.md)
- [Required Headers](/docs/headers.md)
- [Sync/async clients](/docs/sync_async.md)
- [Client as python-package](/docs/client_as_pkg.md)

## Examples
- [Sync](/examples/petstore/client_sync.py) and [async](/examples/petstore/client_async.py) clients for [Petstore OpenAPI](/examples/petstore/openapi.yaml)

## Installing the library and generating clients
By Docker
```shell
docker pull artsmolin/pythogen
docker run -v ./path/to/input:/opt/path/to/input -v ./path/to/output:/opt/path/to/output artsmolin/pythogen path/to/input/openapi.yaml path/to/output/client.py
```
or directly
```shell
pip install pythogen
pythogen path/to/input/openapi.yaml path/to/output/client.py
```
## Usage client
```python
from petstore.client_async import Client
from petstore.client_async import Pet
from petstore.client_async import EmptyBody

client = Client(base_url="http://your.base.url")
pets: list[Pet] | EmptyBody = await client.findPetsByStatus(status="available")
```

[Development](/docs/development.md)
