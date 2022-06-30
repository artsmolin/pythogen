from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict

from pythogen import models
from pythogen.parsers.operations import OperationParser


if TYPE_CHECKING:
    from parsers import SchemaParser
    from references import RefResolver


logger = logging.getLogger(__name__)


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
        openapi_data: Dict[str, Any],
    ) -> None:
        self._openapi_data = openapi_data
        self._ref_resolver = ref_resolver
        self._schema_parser = schema_parser
        self._operation_parser = operation_parser

    def parse_collection(self) -> Dict[str, models.PathItemObject]:
        """Спарсить спецификацию всех ручек из OpenAPI-спеки"""
        parsed_paths: Dict[str, models.PathItemObject] = {}
        paths = self._openapi_data.get('paths', {})
        for path_str, path_item_data in paths.items():
            parsed_paths[path_str] = self.parse_item(path_item_data)
        return parsed_paths

    def parse_item(self, path_data: Dict[str, Any]) -> models.PathItemObject:
        """Спарсить спецификацию ручки"""
        operations = {}

        for method in models.HttpMethod:
            if method.value not in path_data:
                continue

            operation_data = path_data[method.value]
            operations[method] = self._operation_parser.parse_item(method, operation_data)

        return models.PathItemObject(
            summary=path_data.get('summary'),
            description=path_data.get('description'),
            operations=operations,
        )
