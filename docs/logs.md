# Logs
Logging takes place using integration. By default, an instance of class `DefaultLogsIntegration` is used. To set your own logic, you can create your own class that satisfies the base class `BaseLogsIntegration` and pass it to the instance during client initialization.

## Usage with custom integration
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
