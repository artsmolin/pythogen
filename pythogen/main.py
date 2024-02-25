from importlib import metadata
from typing import Optional

import typer
from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename

from pythogen import exceptions
from pythogen import packager
from pythogen import renderer
from pythogen.parsers.document import parse_openapi_file


app = typer.Typer(pretty_exceptions_enable=False)


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
    validate(spec_dict)

    if package_version:
        resp = packager.init_package(
            output_path=output,
            client_class_name=name,
            package_version=package_version,
            package_authors=package_authors,
        )
        output = resp.client_output_path

    try:
        document = parse_openapi_file(input)
    except exceptions.Exit:
        return None

    pythogen_version: str = metadata.version("pythogen")

    renderer.render_client(
        output_path=output,
        document=document,
        name=name,
        sync=sync,
        metrics=metrics,
        required_headers=headers.split(",") if headers else None,
        pythogen_version=pythogen_version,
    )


# Used in pytroject.toml -> [tool.poetry.scripts]
def run() -> None:
    typer.run(main)  # pragma: no cover


if __name__ == "__main__":
    app()
