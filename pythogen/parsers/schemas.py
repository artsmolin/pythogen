import re
from dataclasses import dataclass
from typing import Any
from typing import Optional

from pythogen import models
from pythogen.parsers.references import RefResolver


@dataclass
class ParsedSchema:
    schema: models.SchemaObject
    inline_schemas: dict[str, models.SchemaObject]


@dataclass
class ParsedSchemaColection:
    schemas: dict[str, models.SchemaObject]
    inline_schemas: dict[str, models.SchemaObject]


@dataclass
class ParsedProperties:
    properties: list[models.SchemaProperty]
    inline_schemas: dict[str, models.SchemaObject]


class SchemaParser:
    """Парсер схемы

    Парсит схему из коллекции схем, расположенных в поле components -> schemas
    OpenAPI-спеки (https://swagger.io/specification/#schema-object)

    Пример
    ------
    ```
    components:
      schemas:
        Schema1:
          title: Schema Title
          type: object
          properties:
            property1:
              title: "Property 1"
              type: string
            property2:
              title: "Property 2"
              type: integer
          additionalProperties: false
        Schema2: ...
    ```
    """

    def __init__(
        self,
        ref_resolver: RefResolver,
        openapi_data: dict[str, Any],
        discriminator_base_class_schemas: list[models.DiscriminatorBaseClassSchema],
    ) -> None:
        self._openapi_data = openapi_data
        self._ref_resolver = ref_resolver
        self._discriminator_base_class_schemas = discriminator_base_class_schemas

    def parse_collection(self) -> ParsedSchemaColection:
        schemas_data = self._openapi_data["components"].get('schemas', {})
        schemas = {}
        inline_schemas = {}
        for schema_id, schema_data in schemas_data.items():
            if ref := schema_data.get('$ref', None):
                resolved_ref = self._ref_resolver.resolve(ref)
                parsed_schema = self.parse_item(resolved_ref.ref_id, resolved_ref.ref_data)
            else:
                parsed_schema = self.parse_item(schema_id, schema_data)
            schemas[schema_id] = parsed_schema.schema
            inline_schemas.update(parsed_schema.inline_schemas)
        return ParsedSchemaColection(
            schemas=schemas,
            inline_schemas=inline_schemas,
        )

    def parse_item(self, schema_id: str, schema_data: dict[str, Any]) -> ParsedSchema:
        schema_type = self._parse_type(schema_data)
        parsed_properties = self._parse_properties(schema_type, schema_data)

        discr_schema = self._get_discriminator_base_class_schema(schema_data)
        if discr_schema and discr_schema not in self._discriminator_base_class_schemas:
            self._discriminator_base_class_schemas.append(discr_schema)

        return ParsedSchema(
            schema=models.SchemaObject(
                id=schema_id,
                title=schema_data.get('title'),
                required=schema_data.get('required'),
                enum=schema_data.get('enum'),
                type=schema_type,
                format=self._parse_format(schema_data),
                items=self._parse_items(schema_data),
                properties=parsed_properties.properties,
                description=self._get_description(schema_data),
            ),
            inline_schemas=parsed_properties.inline_schemas,
        )

    def _parse_type(self, data: dict[str, Any]) -> models.Type:
        if data == {}:
            # Парсинг пустой схемы
            # application/json:
            #   schema:
            #     {}
            data_type = models.Type.object
        elif 'allOf' in data:
            data_type = models.Type.object
        elif 'anyOf' in data:
            data_type = models.Type.any_of
        else:
            raw_data_type: str = data.get('type')
            try:
                data_type = models.Type(raw_data_type)
            except ValueError:
                raise Exception(f'Unable to parse schema "{id}", uknown type "{raw_data_type}"')
        return data_type

    def _parse_format(self, data: dict[str, Any]) -> Optional[models.Format]:
        data_format = data.get('format')
        if data_format:
            try:
                return models.Format[data_format.replace('-', '_')]
            except Exception:
                raise Exception(f'Unable to parse schema "{id}", uknown format "{data_format}"')

    def _get_description(self, data: dict[str, Any]) -> Optional[str]:
        description = data.get("description", "")
        if description:
            description = description.replace("\n", "\\n")
            description = description.replace("'", "\\'")
            description = description.replace('"', '\\"')
        return description

    def _get_discriminator_base_class_schema(
        self,
        data: dict[str, Any],
    ) -> Optional[models.DiscriminatorBaseClassSchema]:
        description = data.get("description", "")
        if "__discriminator__" not in description:
            return None
        matches = re.findall(r"(__discriminator__)\((.+)\.(.+)\)", description)
        _, class_name, attr = matches[0]
        return models.DiscriminatorBaseClassSchema(
            name=class_name,
            attr=attr,
        )

    def _parse_properties(self, schema_type: models.Type, data: dict[str, Any]) -> ParsedProperties:
        data_format = data.get('format')
        if data_format:
            try:
                data_format = models.Format[data_format.replace('-', '_')]
            except Exception:
                raise Exception(f'Unable to parse schema "{id}", uknown format "{data_format}"')

        properties = []
        inline_schemas = {}
        if properties_map := data.get('properties'):
            for key, property_schema_data in properties_map.items():
                if ref := property_schema_data.get('$ref', None):
                    resolved_ref = self._ref_resolver.resolve(ref)
                    property_schema_data = resolved_ref.ref_data
                    property_schema_id = resolved_ref.ref_id
                    parsed_schema = self.parse_item(property_schema_id, property_schema_data)
                    schema = parsed_schema.schema
                else:
                    if (
                        property_schema_data.get('type') == models.Type.object.value
                        and 'properties' in property_schema_data
                    ):
                        # extract inline object definition to schema
                        property_schema_id = key + "_obj"
                        parsed_schema = self.parse_item(property_schema_id, property_schema_data)
                        schema = parsed_schema.schema
                    elif 'allOf' in property_schema_data:
                        property_schema_id = key + "_ref_obj"
                        parsed_schema = self.parse_item(property_schema_id, property_schema_data)
                        schema = parsed_schema.schema

                        for all_of_reference_container in property_schema_data['allOf']:
                            ref = all_of_reference_container['$ref']
                            all_of_resolved_ref = self._ref_resolver.resolve(ref)
                            all_of_reference_parsed_schema = self.parse_item(
                                schema_id=all_of_resolved_ref.ref_id,
                                schema_data=all_of_resolved_ref.ref_data,
                            )
                            schema.properties += all_of_reference_parsed_schema.schema.properties

                        inline_schemas[property_schema_id] = schema

                    elif property_schema_data.get('type') == models.Type.array.value:
                        # specify inline array name
                        property_schema_id = key + "_list"
                        parsed_schema = self.parse_item(property_schema_id, property_schema_data)
                        schema = parsed_schema.schema
                    else:
                        property_schema_id = f'<inline+{models.SchemaObject.__name__}>'
                        parsed_schema = self.parse_item(property_schema_id, property_schema_data)
                        schema = parsed_schema.schema

                description = property_schema_data.get("description", "")
                match = re.search(r"(__safety_key__)\((?P<safety_key>.+)\)", description)
                safety_key = match['safety_key'] if match else match

                properties.append(
                    models.SchemaProperty(
                        orig_key=key,
                        safety_key=safety_key,
                        schema=schema,
                    )
                )
        else:
            if schema_type == models.Type.string and not data_format:
                properties.append(
                    models.SchemaProperty(
                        orig_key='text',
                        safety_key=None,
                        schema=models.SchemaObject(
                            id='',
                            type=models.Type.string,
                            enum=None,
                            properties=None,
                            title=None,
                            format=None,
                            items=None,
                            required=None,
                        ),
                    )
                )
            if schema_type == models.Type.string and data_format == models.Format.binary:
                properties.append(
                    models.SchemaProperty(
                        orig_key='content',
                        safety_key=None,
                        schema=models.SchemaObject(
                            id='',
                            type=models.Type.string,
                            enum=None,
                            properties=None,
                            title=None,
                            format=models.Format.binary,
                            items=None,
                            required=None,
                        ),
                    )
                )

        return ParsedProperties(
            properties=properties,
            inline_schemas=inline_schemas,
        )

    def _parse_items(self, data: dict[str, Any]):
        items = None

        if items_schema_data := data.get('items'):
            if ref := items_schema_data.get('$ref', None):
                resolved_ref = self._ref_resolver.resolve(ref)
                parsed_schema = self.parse_item(resolved_ref.ref_id, resolved_ref.ref_data)
                return parsed_schema.schema

            if items_schema_data.get('type') == models.Type.object.value and 'properties' in items_schema_data:
                # extract items object definition to schema
                items_schema_id = id + "_item"
                parsed_schema = self._parse_schema(items_schema_id, items_schema_data)
                return parsed_schema.schema
            else:
                items_schema_id = f'<inline+{models.SchemaObject.__name__}>'
                parsed_schema = self.parse_item(items_schema_id, items_schema_data)
                return parsed_schema.schema

        if any_of := data.get('anyOf'):
            items = []
            for any_ref_item in any_of:
                ref = any_ref_item.get('$ref', None)
                resolved_ref = self._ref_resolver.resolve(ref)
                ref_schema = self.parse_item(resolved_ref.ref_id, resolved_ref.ref_data)
                items.append(ref_schema)
            return items
