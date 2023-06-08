[← README.md](/README.md)

# Required Headers
Pythogen is able to generate a client that will check headers when instantiating. To do this, use the `--headers` flag when generating the client.
If the required headers are not passed to the client, the `RequiredHeaders` exception will be raised.

## Usage
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
