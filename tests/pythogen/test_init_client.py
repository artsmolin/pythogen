import pytest
from tests.clients.async_client_with_headers import Client, RequiredHeaders


def test_init_client_with_headers():
    Client(
        base_url="https://base.url",
        headers={
            "X-API-KEY": "qwerty",
            "X-API-SECRET": "qwerty",
        },
    )


def test_init_client_with_headers_error():
    with pytest.raises(RequiredHeaders):
        Client(
            base_url="https://base.url",
            headers={},
        )