from pathlib import Path
from typer.testing import CliRunner
from contextlib import contextmanager

from pythogen import entrypoint

runner = CliRunner()


OPENAPI_PATH = "tests/docs/openapi.yaml"
ASYNC_CLIENT_PATH = "tests/pythogen/tmp/async_client.py"


@contextmanager
def collect_garbage():
    yield
    Path(ASYNC_CLIENT_PATH).unlink(missing_ok=True)


def test_entrypoint() -> None:
    with collect_garbage():
        result = runner.invoke(entrypoint.app, [OPENAPI_PATH, ASYNC_CLIENT_PATH])
    
    assert result.exit_code == 0
