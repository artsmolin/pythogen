import re
from typing import Any

from pythogen import console
from pythogen import exceptions
from pythogen import models
from pythogen.parsers.references import RefResolver
from pythogen.parsers.schemas import SchemaParser


class ParameterParser:
    def __init__(self, ref_resolver: RefResolver, schema_parser: SchemaParser, openapi_data: dict[str, Any]) -> None:
        self._openapi_data = openapi_data
        self._ref_resolver = ref_resolver
        self._schema_parser = schema_parser

    def parse_collections(self) -> dict[str, models.ParameterObject]:
        parameters = self._openapi_data.get("components", {}).get("parameters", {})
        return {
            parameter_id: self.parse_item(parameter_id, parameter_data)
            for parameter_id, parameter_data in parameters.items()
        }

    def parse_item(self, id_: str, data: dict[str, Any]) -> models.ParameterObject:
        schema_data = data["schema"]
        if schema_data.get("$ref", None):
            resolved_ref = self._ref_resolver.resolve(schema_data["$ref"])
            schema = self._schema_parser.parse_item(resolved_ref.ref_id, resolved_ref.ref_data)
        else:
            schema = self._schema_parser.parse_item(f"<inline+{models.SchemaObject.__name__}>", schema_data)

        description = schema_data.get("description", "")
        match = re.search(r"(__safety_key__)\((?P<safety_key>.+)\)", description)
        safety_key = match["safety_key"] if match else None

        if len(schema.all_of) > 1:
            console.print_error(
                title="Failed to generate a client",
                msg='"allOf" field in property can contains only one item.',
                invalid_data=data,
            )
            raise exceptions.Exit()

        return models.ParameterObject(
            id=id_,
            orig_key=data["name"],
            safety_key=safety_key,
            description=description,
            location=models.ParameterLocation[data["in"]],
            required=data.get("required", False),
            schema=schema,
        )
