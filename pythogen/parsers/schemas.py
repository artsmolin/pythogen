import re
from collections import defaultdict
from typing import Any

from pythogen import models
from pythogen.parsers.inline_schemas_aggregator import InlineSchemasAggregator
from pythogen.parsers.references import RefResolver


PRIMITIVE_TYPES = ('string', 'number', 'integer', 'boolean')


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
        inline_schema_aggregator: InlineSchemasAggregator,
    ) -> None:
        self._openapi_data = openapi_data
        self._ref_resolver = ref_resolver
        self._discriminator_base_class_schemas = discriminator_base_class_schemas
        self._inline_schema_aggregator = inline_schema_aggregator

        self._schema_ids = list(self._openapi_data["components"].get('schemas', {}))
        self._processiong_parsed_schema_id_count: dict[str, int] = defaultdict(int)
        self._schemas: dict[str, models.SchemaObject] = {}

    def parse_collection(self) -> dict[str, models.SchemaObject]:
        schemas_data = self._openapi_data["components"].get('schemas', {})
        for schema_id, schema_data in schemas_data.items():
            if schema_data.get('$ref', None):
                resolved_ref = self._ref_resolver.resolve(schema_data['$ref'])
                schema = self.parse_item(resolved_ref.ref_id, resolved_ref.ref_data)
            else:
                schema = self.parse_item(schema_id, schema_data)

            if not schema.is_fake:
                self._schemas[schema_id] = schema

        return self._schemas

    def parse_item(
        self, schema_id: str, schema_data: dict[str, Any], from_depth_level: bool = False
    ) -> models.SchemaObject:
        """Спарсить схему из OpenAPI-спеки

        Attributes
        ----------
        schema_id
            Идентификатор схемы (ключ в поле components -> schemas)
        schema_data
            Данные схемы
        from_depth_level
            Флаг, указывающий, что схема была спарсена внутри другой схемы.
            Используется для разрешения циклических схем.
        """
        if schema_id in self._schemas:
            return self._schemas[schema_id]
        schema_type = self._parse_type(schema_data)

        self._processiong_parsed_schema_id_count[schema_id] += 1
        if self._processiong_parsed_schema_id_count[schema_id] > 1 and from_depth_level:
            """
            Парсинг циклических схем
            components:
              schemas:
                Schema1:
                  type: object
                  properties:
                    property1:
                      $ref: '#/components/schemas/Schema1'
            """
            return models.SchemaObject(
                id=schema_id,
                title=schema_data.get('title'),
                required=schema_data.get('required'),
                enum=schema_data.get('enum'),
                type=schema_type,
                format=self._parse_format(schema_data),
                items=[],
                properties=[],
                description=self._get_description(schema_data),
                is_fake=True,
            )

        discr_schema = self._get_discriminator_base_class_schema(schema_data)
        if discr_schema and discr_schema not in self._discriminator_base_class_schemas:
            self._discriminator_base_class_schemas.append(discr_schema)

        return models.SchemaObject(
            id=schema_id,
            title=schema_data.get('title'),
            required=schema_data.get('required'),
            enum=schema_data.get('enum'),
            type=schema_type,
            format=self._parse_format(schema_data),
            items=self._parse_items(schema_id, schema_data),
            properties=self._parse_properties(schema_type, schema_data),
            description=self._get_description(schema_data),
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
            raw_data_type: str | None = data.get('type')
            try:
                data_type = models.Type(raw_data_type)
            except ValueError:
                raise Exception(f'Unable to parse schema "{id}", unknown type "{raw_data_type}" on "{data}"')
        return data_type

    def _parse_format(self, data: dict[str, Any]) -> models.Format | None:
        data_format = data.get('format')
        if data_format:
            try:
                return models.Format[data_format.replace('-', '_')]
            except Exception:
                raise Exception(f'Unable to parse schema "{id}", unknown format "{data_format}"')
        return None

    def _get_description(self, data: dict[str, Any]) -> str | None:
        description = data.get("description", "")
        if description:
            description = description.replace("\n", "\\n")
            description = description.replace("'", "\\'")
            description = description.replace('"', '\\"')
        return description

    def _get_discriminator_base_class_schema(
        self,
        data: dict[str, Any],
    ) -> models.DiscriminatorBaseClassSchema | None:
        description = data.get("description", "")
        if "__discriminator__" not in description:
            return None
        matches = re.findall(r"(__discriminator__)\((.+)\.(.+)\)", description)
        _, class_name, attr = matches[0]
        return models.DiscriminatorBaseClassSchema(
            name=class_name,
            attr=attr,
        )

    def _parse_properties(
        self,
        schema_type: models.Type,
        data: dict[str, Any],
    ) -> list[models.SchemaProperty]:
        data_format = data.get('format')
        if data_format:
            try:
                data_format = models.Format[data_format.replace('-', '_')]
            except Exception:
                raise Exception(f'Unable to parse schema "{id}", unknown format "{data_format}"')

        properties = []

        properties_map = data.get('properties')
        if properties_map:
            for key, property_schema_data in properties_map.items():
                if property_schema_data.get('$ref', None):
                    resolved_ref = self._ref_resolver.resolve(property_schema_data['$ref'])
                    property_schema_data = resolved_ref.ref_data
                    property_schema_id = resolved_ref.ref_id
                    schema = self.parse_item(property_schema_id, property_schema_data, from_depth_level=True)
                else:
                    if (
                        property_schema_data.get('type') == models.Type.object.value
                        and 'properties' in property_schema_data
                    ):
                        # extract inline object definition to schema
                        property_schema_id = key + "_obj"
                        schema = self.parse_item(property_schema_id, property_schema_data)
                        self._inline_schema_aggregator.add(property_schema_id, schema)
                    elif 'allOf' in property_schema_data:
                        property_schema_id = key + "_ref_obj"
                        schema = self.parse_item(property_schema_id, property_schema_data)

                        for all_of_reference_container in property_schema_data['allOf']:
                            ref = all_of_reference_container['$ref']
                            all_of_resolved_ref = self._ref_resolver.resolve(ref)
                            all_of_reference_parsed_schema = self.parse_item(
                                schema_id=all_of_resolved_ref.ref_id,
                                schema_data=all_of_resolved_ref.ref_data,
                            )
                            schema.properties += all_of_reference_parsed_schema.properties

                        self._inline_schema_aggregator.add(property_schema_id, schema)

                    elif property_schema_data.get('type') == models.Type.array.value:
                        # specify inline array name
                        property_schema_id = key + "_list"
                        schema = self.parse_item(property_schema_id, property_schema_data)
                    elif 'anyOf' in property_schema_data:
                        # extract inline object definition to schema
                        property_schema_id = key + "_obj"
                        schema = self.parse_item(property_schema_id, property_schema_data)
                        self._inline_schema_aggregator.add(property_schema_id, schema)
                    else:
                        property_schema_id = f'<inline+{models.SchemaObject.__name__}>'
                        schema = self.parse_item(property_schema_id, property_schema_data)

                description = property_schema_data.get("description", "")
                match = re.search(r"(__safety_key__)\((?P<safety_key>.+)\)", description)
                safety_key = match['safety_key'] if match else None

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
                            properties=[],
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
                            properties=[],
                            title=None,
                            format=models.Format.binary,
                            items=None,
                            required=None,
                        ),
                    )
                )

            if schema_type == models.Type.integer:
                properties.append(
                    models.SchemaProperty(
                        orig_key='text',
                        safety_key=None,
                        schema=models.SchemaObject(
                            id='',
                            type=models.Type.integer,
                            enum=None,
                            properties=[],
                            title=None,
                            format=None,
                            items=None,
                            required=None,
                        ),
                    )
                )

        return properties

    def _parse_items(
        self,
        parent_schema_id: str,
        data: dict[str, Any],
    ) -> models.SchemaObject | list[models.SchemaObject] | None:
        items_schema_data = data.get('items')
        if items_schema_data:
            if items_schema_data.get('$ref', None):
                resolved_ref = self._ref_resolver.resolve(items_schema_data['$ref'])
                schema = self.parse_item(resolved_ref.ref_id, resolved_ref.ref_data, from_depth_level=True)
                return schema
            elif items_schema_data.get('anyOf'):
                items = []
                for any_ref_item in items_schema_data['anyOf']:
                    ref = any_ref_item.get('$ref', None)
                    any_ref_any_type = any_ref_item.get('type')
                    if ref:
                        resolved_ref = self._ref_resolver.resolve(ref)
                        ref_schema = self.parse_item(resolved_ref.ref_id, resolved_ref.ref_data, from_depth_level=True)
                        items.append(ref_schema)
                    elif any_ref_any_type in PRIMITIVE_TYPES:
                        items.append(
                            models.SchemaObject(
                                id='',
                                type=models.Type(any_ref_any_type),
                                enum=None,
                                properties=[],
                                title=None,
                                format=None,
                                items=None,
                                required=None,
                            )
                        )
                    else:
                        items_schema_id = f'<inline+{models.SchemaObject.__name__}>'
                        schema = self.parse_item(items_schema_id, items_schema_data)
                        self._inline_schema_aggregator.add(items_schema_id, schema)

                return models.SchemaObject(
                    id='',
                    type=models.Type.any_of,
                    enum=None,
                    properties=[],
                    title=None,
                    format=None,
                    items=items,
                    required=None,
                )
            else:
                parent_raw_type = data.get('type')
                if parent_raw_type == 'array':
                    items_schema_id = f'{parent_schema_id}Item'
                else:
                    items_schema_id = f'<inline+{models.SchemaObject.__name__}>'
                schema = self.parse_item(items_schema_id, items_schema_data)
                if items_schema_data.get('type') not in PRIMITIVE_TYPES:
                    self._inline_schema_aggregator.add(items_schema_id, schema)
                return schema

        if data.get('anyOf'):
            items = []
            for any_ref_item in data['anyOf']:
                ref = any_ref_item.get('$ref', None)
                any_ref_any_type = any_ref_item.get('type')
                if ref:
                    resolved_ref = self._ref_resolver.resolve(ref)
                    ref_schema = self.parse_item(resolved_ref.ref_id, resolved_ref.ref_data, from_depth_level=True)
                    items.append(ref_schema)
                elif any_ref_any_type in PRIMITIVE_TYPES:
                    items.append(
                        models.SchemaObject(
                            id='',
                            type=models.Type(any_ref_any_type),
                            enum=None,
                            properties=[],
                            title=None,
                            format=None,
                            items=None,
                            required=None,
                        )
                    )
                else:
                    items_schema_id = f'<inline+{models.SchemaObject.__name__}>'
                    schema = self.parse_item(items_schema_id, items_schema_data)  # type: ignore
                    self._inline_schema_aggregator.add(items_schema_id, schema)
            return items

        return None
