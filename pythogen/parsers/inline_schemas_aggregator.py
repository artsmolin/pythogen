from typing import Dict

from pythogen.models import SchemaObject


class InlineSchemasAggregator:
    def __init__(self):
        self._id_to_schema_mapping: Dict[str, SchemaObject] = {}

    def add(self, schema_id: str, schema_obj: SchemaObject) -> None:
        # if schema_obj.type is Type.object:
        self._id_to_schema_mapping[schema_id] = schema_obj

    def update(self, id_to_schema_mapping: Dict[str, SchemaObject]) -> None:
        self._id_to_schema_mapping.update(id_to_schema_mapping)

    def get_mapping(self) -> Dict[str, SchemaObject]:
        return self._id_to_schema_mapping
