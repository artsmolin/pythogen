from pathlib import Path
from typer.testing import CliRunner
from contextlib import contextmanager

from pythogen import entrypoint

runner = CliRunner()


OPENAPI_PATH = "tests/docs/openapi.yaml"
TMP_DIR_PATH = "tests/pythogen/tmp"
ASYNC_CLIENT_PATH = f"{TMP_DIR_PATH}/async_client.py"


@contextmanager
def temp_files():
    Path(TMP_DIR_PATH).mkdir(parents=True, exist_ok=True) 
    yield
    Path(ASYNC_CLIENT_PATH).unlink(missing_ok=True)


def test_entrypoint() -> None:
    with temp_files():
        result = runner.invoke(entrypoint.app, [OPENAPI_PATH, ASYNC_CLIENT_PATH])
    
    assert result.exit_code == 0
