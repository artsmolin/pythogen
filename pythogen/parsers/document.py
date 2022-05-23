from __future__ import annotations

import logging

import yaml

from pythogen import models
from pythogen.parsers.operations import OperationParser
from pythogen.parsers.parameters import ParameterParser
from pythogen.parsers.paths import PathParser
from pythogen.parsers.references import RefResolver
from pythogen.parsers.request_body import RequestBodyParser
from pythogen.parsers.response import ResponseParser
from pythogen.parsers.schemas import SchemaParser


logger = logging.getLogger(__name__)


def parse_openapi_file(file_path: str) -> models.Document:
    """Корневой парсер OpenAPI-файла

    Парсит файл и возвращает его представление в виде pydantic-объекта.

    Parameters
    ----------
    file_path
        Путь до OpenAPI-файла, который необходимо спарсить.
    """
    with open(file_path) as file:
        openapi_data = yaml.load(file, yaml.SafeLoader)

    # Сюда будут складываться найденные в процессе парсинга базовые классы,
    # в которых определён дискриминатор.
    discriminator_base_class_schemas = []

    ref_resolver = RefResolver(
        openapi_data=openapi_data,
    )
    schema_parser = SchemaParser(
        ref_resolver=ref_resolver,
        openapi_data=openapi_data,
        discriminator_base_class_schemas=discriminator_base_class_schemas,
    )
    response_parser = ResponseParser(
        ref_resolver=ref_resolver,
        schema_parser=schema_parser,
    )
    request_body_parser = RequestBodyParser(
        ref_resolver=ref_resolver,
        schema_parser=schema_parser,
    )
    parameters_parser = ParameterParser(
        ref_resolver=ref_resolver,
        schema_parser=schema_parser,
        openapi_data=openapi_data,
    )
    operation_parser = OperationParser(
        ref_resolver=ref_resolver,
        schema_parser=schema_parser,
        response_parser=response_parser,
        request_body_parser=request_body_parser,
        parameters_parser=parameters_parser,
    )
    path_parser = PathParser(
        ref_resolver=ref_resolver,
        schema_parser=schema_parser,
        operation_parser=operation_parser,
        openapi_data=openapi_data,
    )

    parsed_paths = path_parser.parse_collection()
    parsed_schemas = schema_parser.parse_collection()
    schemas: dict[str, models.SchemaObject] = {
        **parsed_schemas.schemas,
        **parsed_schemas.inline_schemas,
        **parsed_paths.inline_schemas,
    }

    document = models.Document(
        info=models.InfoObject(
            title=openapi_data['info']['title'],
            version=openapi_data['info']['version'],
        ),
        paths=parsed_paths.paths,
        schemas=schemas,
        parameters=parameters_parser.parse_collections(),
        discriminator_base_class_schemas=discriminator_base_class_schemas,
    )
    # print(document)
    return document
