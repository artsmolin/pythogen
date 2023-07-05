Generator of python HTTP-clients from OpenApi specification based on [httpx](https://github.com/projectdiscovery/httpx) and [pydantic](https://github.com/pydantic/pydantic).


[![Build Status](https://github.com/artsmolin/pythogen/actions/workflows/main.yml/badge.svg)](https://github.com/artsmolin/pythogen/actions)
[![codecov](https://codecov.io/gh/artsmolin/pythogen/branch/main/graph/badge.svg?token=6JR6NB8Y9Z)](https://codecov.io/gh/artsmolin/pythogen)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![downloads](https://pepy.tech/badge/pythogen/month)](https://pepy.tech/project/pythogen)
[![python](https://img.shields.io/pypi/pyversions/pythogen.svg)](https://pypi.python.org/pypi/pythogen/)
[![pypi](https://img.shields.io/pypi/v/pythogen.svg)](https://pypi.org/project/pythogen/)
[![license](https://img.shields.io/github/license/artsmolin/pythogen.svg)](https://github.com/artsmolin/pythogen/blob/master/LICENSE)

---

<p align="center">
  <img src="https://github.com/artsmolin/pythogen/raw/main/docs/images/example.png">
</p>

- [Installation](#installation)
- [Generation](#generation)
- [Usage](#usage)
- [Metrics](#metrics)
- [Required Headers](#required-headers)
- [Sync/async client](#syncasync-client)
- [Generate client as python-package](#generate-client-as-python-package)
- [Logs](#logs)
- [Discriminator](#discriminator)
- [Examples](#examples)

## Installation
Pip
```shell
pip install pythogen
```
Docker
```shell
docker pull artsmolin/pythogen
```

## Generation
- `path/to/input` — path to the directory with openapi.yaml;
- `path/to/output` — the path to the directory where the generated client will be saved;

Pip
```shell
pythogen path/to/input/openapi.yaml path/to/output/client.py
```
Docker
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

client = Client(base_url="http://your.base.url")
pets: list[Pet] | EmptyBody = await client.findPetsByStatus(status="available")
```

## Metrics
Pythogen is capable of generating a base class to integrate metrics into the client. To do this, use the `--metrics` flag when generating the client. The `BaseMetricsIntegration` and `DefaultMetricsIntegration` classes will be generated.

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

## Required Headers
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

## Sync/async client
Asynchronous client
```shell
pythogen path/to/input/openapi.yaml path/to/output/client.py
```

Synchronous client
```shell
pythogen path/to/input/openapi.yaml path/to/output/client.py --sync
```

## Generate client as python-package
```shell
pythogen path/to/input/openapi.yaml path/to/package/output --package-version=0.0.1 --package-authors="Rick, Morty"
```
- `--package-version` — required;
- `--package-authors` — optional;
- `path/to/package/output` — path to the directory where package will be saved.

## Logs
Logging takes place using integration. By default, an instance of class `DefaultLogsIntegration` is used. To set your own logic, you can create your own class that satisfies the base class `BaseLogsIntegration` and pass it to the instance during client initialization.

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

## Discriminator
Pythogen is able to generate a base class in which the logic of the discriminator is implemented by the value of the specified field. To do this, the desired field in the "description" parameter must contain a text
```
__discriminator__(BaseClassName.field)
```
- `BaseClassName` — desired name of the base class
- `field` — discriminator field

## Examples
- [Sync](/examples/petstore/client_sync.py) and [async](/examples/petstore/client_async.py) clients for [Petstore OpenAPI](/examples/petstore/openapi.yaml)
