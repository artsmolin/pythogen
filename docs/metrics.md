[← README.md](/README.md)

# Metrics
Pythogen is capable of generating a base class to integrate metrics into the client. To do this, use the `--metrics` flag when generating the client. The `BaseMetricsIntegration` and `DefaultMetricsIntegration` classes will be generated.

## Usage
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
