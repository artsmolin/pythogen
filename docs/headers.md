[← README.md](/README.md)

# Required Headers
Pythogen is able to generate a client that will check headers when instantiating. To do this, use the `--headers` flag when generating the client.
If the required headers are not passed to the client, the `RequiredHeaders` exception will be raised.

## Usage
```shell
pythogen path/to/input/openapi.yaml path/to/output/client.py --headers "X-API-KEY,X-API-SECRET"
```
