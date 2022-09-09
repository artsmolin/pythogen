"""
Точка входа. Запуск генератора клиента происходит отсюда.
"""


from typing import Optional

import typer

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
):
    """
    Generate HTTP clients for python from OpenAPI
    """
    if package_version:
        resp = packager.init_package(
            output_path=output,
            client_class_name=name,
            package_version=package_version,
            package_authors=package_authors,
        )
        output = resp.client_output_path

    document = parse_openapi_file(input)

    renderer.render_client(
        output_path=output,
        document=document,
        name=name,
        sync=sync,
        metrics=metrics,
    )


def run() -> None:
    typer.run(main)


if __name__ == '__main__':
    app()
