from pathlib import Path
import pytest
from typer.testing import CliRunner
from contextlib import contextmanager

from pythogen import main

runner = CliRunner()


OPENAPI_PATH = "tests/docs/openapi.yaml"
TMP_DIR_PATH = "tests/pythogen/tmp"
ASYNC_CLIENT_PATH = f"{TMP_DIR_PATH}/async_client.py"
ASYNC_CLIENT_PKG_PATH = f"{TMP_DIR_PATH}/async_client_pkg"


@pytest.fixture
def temp_files():
    Path(TMP_DIR_PATH).mkdir(parents=True, exist_ok=True) 
    yield
    try:
        Path(ASYNC_CLIENT_PATH).unlink()
    except FileNotFoundError:
        pass


@pytest.mark.usefixtures("temp_files")
def test_entrypoint_gen_http_client() -> None:
    result = runner.invoke(main.app, [OPENAPI_PATH, ASYNC_CLIENT_PATH])
    assert result.exit_code == 0


@pytest.mark.usefixtures("temp_files")
def test_entrypoint_gen_http_client_pkg() -> None:
    result = runner.invoke(main.app, [OPENAPI_PATH, ASYNC_CLIENT_PKG_PATH, "--package-version", "0.0.1"])
    assert result.exit_code == 0
