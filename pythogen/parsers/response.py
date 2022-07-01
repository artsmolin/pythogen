import logging
from typing import Any
from typing import Dict

from pythogen import models
from pythogen.parsers.inline_schemas_aggregator import InlineSchemasAggregator
from pythogen.parsers.references import RefResolver
from pythogen.parsers.schemas import SchemaParser


logger = logging.getLogger(__name__)


class ResponseParser:
    def __init__(
        self,
        ref_resolver: RefResolver,
        schema_parser: SchemaParser,
        inline_schema_aggregator: InlineSchemasAggregator,
    ) -> None:
        self._ref_resolver = ref_resolver
        self._schema_parser = schema_parser
        self._inline_schema_aggregator = inline_schema_aggregator

    def parse_item(self, response_id: str, response_data: Dict[str, Any]) -> models.ResponseObject:
        """Спарсить спецификацию ответа ручки"""
        schema = None

        content = response_data.get('content')
        if content:
            media_types = list(content.keys())
            if len(media_types) > 1:
                logger.error(f'Unable to parse response "{response_id}", multiple media types not implemented yet')
            media_type = media_types[0]
            media_type_data = content[media_type]
            schema_data = media_type_data['schema']

            if schema_data.get('$ref', None):
                resolved_ref = self._ref_resolver.resolve(schema_data['$ref'])
                schema = self._schema_parser.parse_item(resolved_ref.ref_id, resolved_ref.ref_data)
            else:
                schema = self._schema_parser.parse_item(response_id, schema_data)
                self._inline_schema_aggregator.add(response_id, schema)

        return models.ResponseObject(
            id=response_id,
            description=response_data['description'],
            schema=schema,
        )
