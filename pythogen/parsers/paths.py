from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any

from pythogen import models
from pythogen.parsers.operations import OperationParser


if TYPE_CHECKING:
    from parsers import SchemaParser
    from references import RefResolver


logger = logging.getLogger(__name__)


@dataclass
class ParsedPaths:
    paths: dict[str, models.PathItemObject]
    inline_schemas: dict[str, models.SchemaObject]


@dataclass
class ParsedPath:
    path: models.PathItemObject
    inline_schemas: dict[str, models.SchemaObject]


class PathParser:
    """Парсер путей

    Парсит пути из коллекции путей, расположенных в поле paths
    OpenAPI-спеки (https://swagger.io/specification/#paths-object)

    Пример
    ------
    ```
    paths:
    /pets:
        get:
            description: Returns all pets
            responses:
            '200':
                description: A list of pets.
                content:
                application/json:
                    schema:
                    type: array
                    items:
                        $ref: '#/components/schemas/Pet'
    ```
    """

    def __init__(
        self,
        ref_resolver: RefResolver,
        schema_parser: SchemaParser,
        operation_parser: OperationParser,
        openapi_data: dict[str, Any],
    ) -> None:
        self._openapi_data = openapi_data
        self._ref_resolver = ref_resolver
        self._schema_parser = schema_parser
        self._operation_parser = operation_parser

    def parse_collection(self) -> ParsedPaths:
        """Спарсить спецификацию всех ручек из OpenAPI-спеки"""
        parsed_paths = {}
        inline_schemas = {}
        paths = self._openapi_data.get('paths', {})
        for path_str, path_item_data in paths.items():
            parsed_path = self.parse_item(path_item_data)
            parsed_paths[path_str] = parsed_path.path
            inline_schemas.update(parsed_path.inline_schemas)

        return ParsedPaths(
            paths=parsed_paths,
            inline_schemas=inline_schemas,
        )

    def parse_item(self, path_data: dict[str, Any]) -> ParsedPath:
        """Спарсить спецификацию ручки"""
        operations = {}
        inline_schemas = {}

        for method in models.HttpMethod:
            if method.value not in path_data:
                continue

            operation_data = path_data[method.value]
            parsed_operation = self._operation_parser.parse_item(method, operation_data)
            operations[method] = parsed_operation.operation
            inline_schemas.update(parsed_operation.inline_schemas)

        return ParsedPath(
            path=models.PathItemObject(
                summary=path_data.get('summary'),
                description=path_data.get('description'),
                operations=operations,
            ),
            inline_schemas=inline_schemas,
        )
