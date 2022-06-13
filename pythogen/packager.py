"""
Отвечает за всё, что необходимо сделать (сгенерировать файлы
зависимостей, инициализаций, конфигураций), чтобы сгенерированный
клиент можно было упаковать в пакет.
"""

import dataclasses
from pathlib import Path
from typing import Optional

from jinja2 import Environment
from jinja2 import FileSystemLoader

from pythogen import settings


@dataclasses.dataclass
class InitPackageResponse:
    client_output_path: str


def init_package(
    *,
    output_path: str,
    client_class_name: str,
    package_version: str,
    package_authors: Optional[str] = None,
) -> InitPackageResponse:
    package_name = f"{client_class_name.lower().replace('client', '')}_client"

    pyproject_path = Path(output_path).joinpath(package_name)
    pyproject_path.mkdir(parents=True, exist_ok=True)
    _create_pyproject_file(pyproject_path, package_name, package_version, package_authors)

    sources_path = pyproject_path.joinpath(package_name)
    sources_path.mkdir(parents=True, exist_ok=True)
    _create_init_file(sources_path, package_name)

    return InitPackageResponse(client_output_path=str(sources_path.joinpath(f'{package_name}.py')))


def _create_pyproject_file(output_dir: Path, package_name: str, version: str, authors: Optional[str] = None) -> None:
    env = Environment(
        loader=FileSystemLoader(settings.TEMPLATES_DIR_PATH),
        extensions=['jinja2.ext.loopcontrols'],
    )
    template = env.get_template('pyproject-toml.j2')

    pyproject_path = output_dir.joinpath('pyproject.toml')

    with open(pyproject_path, 'w') as pyproject_file:
        pyproject_file.write(
            template.render(
                name=package_name,
                version=version,
                authors=authors,
            )
        )


def _create_init_file(output_dir: Path, module_name: str) -> None:
    env = Environment(
        loader=FileSystemLoader(settings.TEMPLATES_DIR_PATH),
        extensions=['jinja2.ext.loopcontrols'],
    )
    template = env.get_template('init-py.j2')

    init_path = output_dir.joinpath('__init__.py')

    with open(init_path, 'w') as init_file:
        init_file.write(
            template.render(
                module_name=module_name,
            )
        )
