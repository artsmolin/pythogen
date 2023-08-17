"""
Точка входа. Запуск генератора клиента происходит отсюда.
"""


from pathlib import Path
from typing import Optional

import toml
import typer
from openapi_spec_validator import validate_spec
from openapi_spec_validator.readers import read_from_filename

from pythogen import packager
from pythogen import renderer
from pythogen.parsers.document import parse_openapi_file


app = typer.Typer()


@app.command()
def main(
    input: str = typer.Argument(..., help="input OpenAPI file path"),
    output: str = typer.Argument(..., help="client output file path"),
    name: str = typer.Option("Client", help="client class name"),
    sync: bool = typer.Option(False, help="sync client"),
    package_version: Optional[str] = typer.Option(None, help="package version"),
    package_authors: Optional[str] = typer.Option(None, help="package authors"),
    metrics: bool = typer.Option(False, help="include metrics integration"),
    headers: Optional[str] = typer.Option(None, help="required headers"),
):
    """
    Generate HTTP clients for python from OpenAPI
    """
    spec_dict, _ = read_from_filename(input)
    validate_spec(spec_dict)

    if package_version:
        resp = packager.init_package(
            output_path=output,
            client_class_name=name,
            package_version=package_version,
            package_authors=package_authors,
        )
        output = resp.client_output_path

    document = parse_openapi_file(input)

    pyproject_path = Path(__file__).parent.parent.absolute() / Path("pyproject.toml")
    with open(pyproject_path, "r") as f:
        pyproject_data = toml.load(f)

    pythogen_version: str = pyproject_data["tool"]["poetry"]["version"]

    renderer.render_client(
        output_path=output,
        document=document,
        name=name,
        sync=sync,
        metrics=metrics,
        required_headers=headers.split(",") if headers else None,
        pythogen_version=pythogen_version,
    )


def run() -> None:
    typer.run(main)


if __name__ == '__main__':
    app()
