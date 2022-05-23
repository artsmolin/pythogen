import logging
from dataclasses import dataclass
from typing import Any

from pythogen import models
from pythogen.parsers.references import RefResolver
from pythogen.parsers.schemas import SchemaParser


logger = logging.getLogger(__name__)


@dataclass
class ParsedResponse:
    response: models.ResponseObject
    inline_schemas: dict[str, models.SchemaObject]


class ResponseParser:
    def __init__(self, ref_resolver: RefResolver, schema_parser: SchemaParser) -> None:
        self._ref_resolver = ref_resolver
        self._schema_parser = schema_parser

    def parse_item(self, response_id: str, response_data: dict[str, Any]) -> ParsedResponse:
        """Спарсить спецификацию ответа ручки"""
        schema = None
        inline_schemas: dict[str, models.SchemaObject] = {}

        if content := response_data.get('content'):
            media_types = list(content.keys())
            if len(media_types) > 1:
                logger.error(f'Unable to parse response "{response_id}", multiple media types not implemented yet')
            media_type = media_types[0]
            media_type_data = content[media_type]
            schema_data = media_type_data['schema']

            if ref := schema_data.get('$ref', None):
                resolved_ref = self._ref_resolver.resolve(ref)
                parsed_schema = self._schema_parser.parse_item(resolved_ref.ref_id, resolved_ref.ref_data)
                schema = parsed_schema.schema
            else:
                parsed_schema = self._schema_parser.parse_item(response_id, schema_data)
                inline_schemas[response_id] = parsed_schema.schema
                schema = parsed_schema.schema

        return ParsedResponse(
            response=models.ResponseObject(
                id=response_id,
                description=response_data['description'],
                schema=schema,
            ),
            inline_schemas=inline_schemas,
        )
