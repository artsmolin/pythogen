"""
Точка входа. Запуск генератора клиента происходит отсюда.
"""


from typing import Optional

import typer

from pythogen import packager
from pythogen import renderer
from pythogen.parsers.document import parse_openapi_file


def main(
    input: str = typer.Argument(..., help="input OpenAPI file path"),
    output: str = typer.Argument(..., help="client output file path"),
    name: str = typer.Option("Client", help="client class name"),
    sync: bool = typer.Option(False, help="sync client"),
    package: Optional[str] = typer.Option(None, help="package version"),
):
    """
    Generate HTTP clients for python from OpenAPI
    """

    if package:
        resp = packager.init_package(client_class_name=name, package_version=package)
        output = resp.output_path

    document = parse_openapi_file(input)

    renderer.render_client(
        output_path=output,
        document=document,
        name=name,
        sync=sync,
    )


def run() -> None:
    typer.run(main)


if __name__ == '__main__':
    run()
