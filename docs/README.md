Generator of python HTTP-clients from OpenApi specification based on [httpx](https://github.com/projectdiscovery/httpx) and [pydantic](https://github.com/pydantic/pydantic).


[![codecov](https://codecov.io/gh/artsmolin/pythogen/branch/main/graph/badge.svg?token=6JR6NB8Y9Z)](https://codecov.io/gh/artsmolin/pythogen)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![downloads](https://img.shields.io/pypi/dm/pythogen)
[![python](https://img.shields.io/pypi/pyversions/pythogen.svg)](https://pypi.python.org/pypi/pythogen/)
[![pypi](https://img.shields.io/pypi/v/pythogen.svg)](https://pypi.org/project/pythogen/)
[![license](https://img.shields.io/github/license/artsmolin/pythogen.svg)](https://github.com/artsmolin/pythogen/blob/master/LICENSE)

- [Overview](#overview)
  - [Installation](#installation)
  - [Generation](#generation)
  - [Usage](#usage)
- [Features](#features)
  - [Metrics](#metrics)
  - [Required Headers](#required-headers)
  - [Sync/async client](#syncasync-client)
  - [Generate client as python-package](#generate-client-as-python-package)
  - [Logs](#logs)
  - [Discriminator](#discriminator)
- [Examples](#examples)

## Overview
### Installation
You can install the library
```shell
pip install pythogen
```
or use Docker
```shell
docker pull artsmolin/pythogen
```

### Generation
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

### Usage
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

## Features
### Metrics
Pythogen is capable of generating a base class to integrate metrics into the client. To do this, use the `--metrics` flag when generating the client. The `DefaultMetricsIntegration` class will be generated. You can use it, or create your own class that satisfies the `MetricsIntegration` protocol and pass it to the instance during client initialization.

```python
from prometheus_client import Counter
from prometheus_client import Histogram

from petstore.client_async import Client
from petstore.client_async import Pet
from petstore.client_async import EmptyBody
from petstore.client_async import DefaultMetricsIntegration


client_response_time = Histogram(
    'http_client_duration',
    'http_client_duration requests to external services duration in seconds',
    labelnames=(
        'client_name',
        'http_method',
        'http_target',
        'http_status_code',
    ),
)

client_non_http_errors = Counter(
    'http_client_other_errors_total',
    'http_client_other_errors_total total count of non http errors occurred',
    labelnames=(
        'client_name',
        'http_method',
        'http_target',
        'exception',
    ),
)


client = Client(
    base_url="http://your.base.url",
    metrics_integration=DefaultMetricsIntegration(
        client_response_time_histogram=client_response_time,
        client_non_http_errors_counter=client_non_http_errors,
    ),
)
```

### Required Headers
Pythogen is able to generate a client that will check headers when instantiating. To do this, use the `--headers` flag when generating the client.
If the required headers are not passed to the client, the `RequiredHeaders` exception will be raised.

Client generating
```shell
pythogen path/to/input/openapi.yaml path/to/output/client.py --headers "X-API-KEY,X-API-SECRET"
```
Client instantiating
```python
client = Client(
    base_url="http://your.base.url",
    headers={
        "X-API-KEY": "qwerty",
        "X-API-SECRET": "qwerty1234",
    },
)
```

### Sync/async client
Asynchronous client
```shell
pythogen path/to/input/openapi.yaml path/to/output/client.py
```

Synchronous client
```shell
pythogen path/to/input/openapi.yaml path/to/output/client.py --sync
```

### Generate client as python-package
```shell
pythogen path/to/input/openapi.yaml path/to/package/output --package-version=0.0.1 --package-authors="Rick, Morty"
```
- `--package-version` — required;
- `--package-authors` — optional;
- `path/to/package/output` — path to the directory where package will be saved.

### Logs
Logging takes place using integration. By default, an instance of class `DefaultLogsIntegration` is used. To set your own logic, you can create your own class that satisfies the `LogsIntegration` protocol and pass it to the instance during client initialization.

Usage with custom integration
```python
import logging

from petstore.client_async import Client
from petstore.client_async import Pet
from petstore.client_async import EmptyBody
from petstore.client_async import DefaultLogsIntegration


class CustomLogsIntegration(DefaultLogsIntegration):
    def get_log_level(self, req: RequestBox, resp: ResponseBox) -> int:
        # your logic
        ...


client = Client(
    base_url="http://your.base.url",
    logs_integration=CustomLogsIntegration(),
)
```

### Discriminator
Generate [pydantic classes with discriminators](https://docs.pydantic.dev/latest/api/standard_library_types/#discriminated-unions-aka-tagged-unions) based on [OpenAPI discriminators](https://swagger.io/docs/specification/data-models/inheritance-and-polymorphism/). The original OpenAPI specification must have the propertyName and mapping fields.

## Examples
- [Sync](/examples/petstore/client_sync.py) and [async](/examples/petstore/client_async.py) clients for [Petstore OpenAPI](/examples/petstore/openapi.yaml)
