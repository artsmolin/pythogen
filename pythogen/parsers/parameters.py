import re
from typing import Any
from typing import Dict

from pythogen import models
from pythogen.parsers.references import RefResolver
from pythogen.parsers.schemas import SchemaParser


class ParameterParser:
    def __init__(self, ref_resolver: RefResolver, schema_parser: SchemaParser, openapi_data: Dict[str, Any]) -> None:
        self._openapi_data = openapi_data
        self._ref_resolver = ref_resolver
        self._schema_parser = schema_parser

    def parse_collections(self) -> Dict[str, models.ParameterObject]:
        parameters = self._openapi_data["components"].get('parameters', {})
        result = {}
        for parameter_id, parameter_data in parameters.items():
            if parameter_data.get('$ref', None):
                parameter = self.parse_item_from_ref(parameter_id, parameter_data['$ref'])
            else:
                parameter = self.parse_item(parameter_id, parameter_data)
            result[parameter_id] = parameter
        return result

    def parse_item_from_ref(self, id_: str, ref: str) -> models.ParameterObject:
        resolved_ref = self._ref_resolver.resolve(ref)
        return self.parse_item(id_, resolved_ref.ref_data)

    def parse_item(self, id_: str, data: Dict[str, Any]) -> models.ParameterObject:
        schema_data = data['schema']
        if schema_data.get('$ref', None):
            resolved_ref = self._ref_resolver.resolve(schema_data['$ref'])
            schema = self._schema_parser.parse_item(resolved_ref.ref_id, resolved_ref.ref_data)
        else:
            schema = self._schema_parser.parse_item(f'<inline+{models.SchemaObject.__name__}>', schema_data)

        description = schema_data.get('description', '')
        match = re.search(r"(__safety_key__)\((?P<safety_key>.+)\)", description)
        safety_key = match['safety_key'] if match else None

        return models.ParameterObject(
            id=id_,
            orig_key=data['name'],
            safety_key=safety_key,
            description=description,
            location=models.ParameterLocation[data['in']],
            required=data.get('required', False),
            schema=schema,
        )
