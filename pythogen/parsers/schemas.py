import re
from collections import defaultdict
from typing import Any

from pythogen import console
from pythogen import exceptions
from pythogen import models
from pythogen.parsers.inline_schemas_aggregator import InlineSchemasAggregator
from pythogen.parsers.references import RefResolver


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

        self._processiong_parsed_schema_id_count: dict[str, int] = defaultdict(int)
        self._schemas: dict[str, models.SchemaObject] = {}

    def parse_collection(self) -> dict[str, models.SchemaObject]:
        schemas_data = self._openapi_data.get("components", {}).get("schemas", {})
        for schema_id, schema_data in schemas_data.items():
            if schema_data.get("$ref", None):
                resolved_ref = self._ref_resolver.resolve(schema_data["$ref"])
                schema = self.parse_item(resolved_ref.ref_id, resolved_ref.ref_data)
            else:
                schema = self.parse_item(schema_id, schema_data)

            if not schema.is_fake:
                self._schemas[schema_id] = schema

        return self._schemas

    def parse_item(
        self, schema_id: str, schema_data: dict[str, Any], from_depth_level: bool = False, is_inline: bool = False
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
        all_of = self._parse_all_of(schema_id, schema_data)
        any_of = self._parse_any_of(schema_id, schema_data)

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
                title=schema_data.get("title"),
                required=schema_data.get("required", []),
                enum=schema_data.get("enum"),
                type=schema_type,
                format=self._parse_format(schema_data),
                items=[],
                properties=[],
                description=self._get_description(schema_data),
                is_fake=True,
                all_of=all_of,
                any_of=any_of,
                is_inline=is_inline,
                discriminator=self._parse_discriminator(schema_data),
                minimum=schema_data.get("minimum"),
                maximum=schema_data.get("maximum"),
                exclusive_minimum=schema_data.get("exclusiveMinimum", False),
                exclusive_maximum=schema_data.get("exclusiveMaximum", False),
            )

        discr_schema = self._get_discriminator_base_class_schema(schema_data)
        if discr_schema and discr_schema not in self._discriminator_base_class_schemas:
            self._discriminator_base_class_schemas.append(discr_schema)

        return models.SchemaObject(
            id=schema_id,
            title=schema_data.get("title"),
            required=schema_data.get("required", []),
            enum=schema_data.get("enum"),
            type=schema_type,
            format=self._parse_format(schema_data),
            items=self._parse_items(schema_id, schema_data),
            properties=self._parse_properties(schema_id, schema_type, schema_data),
            description=self._get_description(schema_data),
            all_of=all_of,
            any_of=any_of,
            is_inline=is_inline,
            discriminator=self._parse_discriminator(schema_data),
            minimum=schema_data.get("minimum"),
            maximum=schema_data.get("maximum"),
            exclusive_minimum=schema_data.get("exclusiveMinimum", False),
            exclusive_maximum=schema_data.get("exclusiveMaximum", False),
        )

    def _parse_all_of(self, parent_id: str, parent_data: dict[str, Any]) -> list[models.SchemaObject]:
        result: list[models.SchemaObject] = []
        for i, all_of_item in enumerate(parent_data.get("allOf", [])):
            if ref := all_of_item.get("$ref"):
                resolved_ref = self._ref_resolver.resolve(ref)
                all_of_item_schema = self.parse_item(resolved_ref.ref_id, resolved_ref.ref_data, from_depth_level=True)
                result.append(all_of_item_schema)
            else:
                all_of_item_schema_id = f"{parent_id}_item_{i}"
                all_of_item_schema = self.parse_item(
                    all_of_item_schema_id, all_of_item, from_depth_level=True, is_inline=True
                )
                self._inline_schema_aggregator.add(all_of_item_schema_id, all_of_item_schema)
                result.append(all_of_item_schema)

        return result

    def _parse_any_of(self, parent_id: str, parent_data: dict[str, Any]) -> list[models.SchemaObject]:
        result: list[models.SchemaObject] = []
        for i, any_of_item in enumerate(parent_data.get("anyOf", [])):
            if ref := any_of_item.get("$ref"):
                resolved_ref = self._ref_resolver.resolve(ref)
                any_of_item_schema = self.parse_item(resolved_ref.ref_id, resolved_ref.ref_data, from_depth_level=True)
                result.append(any_of_item_schema)
            else:
                any_of_item_schema_id = f"{parent_id}_item_{i}"
                any_of_item_schema = self.parse_item(any_of_item_schema_id, any_of_item, from_depth_level=True)
                self._inline_schema_aggregator.add(any_of_item_schema_id, any_of_item_schema)
                result.append(any_of_item_schema)

        return result

    def _parse_type(self, data: dict[str, Any]) -> models.Type:
        if data == {}:
            # Парсинг пустой схемы
            # application/json:
            #   schema:
            #     {}
            data_type = models.Type.object
        elif "allOf" in data:
            data_type = models.Type.object
        elif "anyOf" in data:
            data_type = models.Type.object
        elif "type" not in data:
            data_type = models.Type.object
        else:
            raw_data_type: str | None = data.get("type")
            try:
                data_type = models.Type(raw_data_type)
            except ValueError as exc:
                raise Exception(f'Unable to parse schema, unknown type "{raw_data_type}" on "{data}"') from exc
        return data_type

    def _parse_format(self, data: dict[str, Any]) -> models.Format | None:
        data_format = data.get("format")
        if data_format:
            try:
                return models.Format(data_format)
            except Exception as exc:
                raise Exception(f'Unable to parse schema, unknown format "{data_format}"') from exc
        return None

    def _get_description(self, data: dict[str, Any]) -> str | None:
        description = data.get("description", "")
        if description:
            description = description.replace("\n", "\\n")
            description = description.replace("'", "\\'")
            description = description.replace('"', '\\"')
        return description

    def _parse_discriminator(self, data: dict[str, Any]) -> models.Discriminator | None:
        raw_discriminator: dict[str, Any] | None = data.get("discriminator")

        if not raw_discriminator:
            return None

        property_name: str | None = raw_discriminator.get("propertyName")
        if not property_name:
            console.print_error(
                title="Failed to generate a client",
                msg='The discriminator must contain the "propertyName" field.',
                invalid_data=data,
            )
            raise exceptions.Exit()

        raw_mapping: dict[str, Any] | None = raw_discriminator.get("mapping")
        if not raw_mapping:
            console.print_error(
                title="Failed to generate a client",
                msg='The discriminator must contain the "mapping" field.',
                invalid_data=data,
            )
            raise exceptions.Exit()

        mapping: dict[str, models.SchemaObject] = {}
        for discriminator_value, ref in raw_mapping.items():
            resolved_ref = self._ref_resolver.resolve(ref)
            schema = self.parse_item(resolved_ref.ref_id, resolved_ref.ref_data, from_depth_level=True)
            mapping[discriminator_value] = schema

        return models.Discriminator(
            property_name=property_name,
            mapping=mapping,
        )

    # TODO: remove
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
        parent_schema_id: str,
        schema_type: models.Type,
        data: dict[str, Any],
    ) -> list[models.SchemaProperty]:
        data_format = data.get("format")
        if data_format:
            try:
                data_format = models.Format(data_format)
            except Exception as exc:
                raise Exception(f'Unable to parse schema "{id}", unknown format "{data_format}"') from exc

        properties = []

        properties_map = data.get("properties")
        if properties_map:
            for key, property_schema_data in properties_map.items():
                if property_schema_data.get("$ref", None):
                    resolved_ref = self._ref_resolver.resolve(property_schema_data["$ref"])
                    property_schema_data = resolved_ref.ref_data
                    property_schema_id = resolved_ref.ref_id
                    schema = self.parse_item(property_schema_id, property_schema_data, from_depth_level=True)
                else:
                    if (
                        property_schema_data.get("type") == models.Type.object.value
                        and "properties" in property_schema_data
                    ):
                        # extract inline object definition to schema
                        property_schema_id = key + "_obj"
                        schema = self.parse_item(property_schema_id, property_schema_data)
                        self._inline_schema_aggregator.add(property_schema_id, schema)
                    elif "allOf" in property_schema_data:
                        property_schema_id = key + "_ref_obj"
                        schema = self.parse_item(property_schema_id, property_schema_data)
                        self._inline_schema_aggregator.add(property_schema_id, schema)
                    elif property_schema_data.get("type") == models.Type.array.value:
                        # specify inline array name
                        property_schema_id = key + "_list"
                        schema = self.parse_item(property_schema_id, property_schema_data)
                    elif "anyOf" in property_schema_data:
                        # extract inline object definition to schema
                        property_schema_id = parent_schema_id + "_" + key + "_obj"
                        schema = self.parse_item(property_schema_id, property_schema_data)
                        self._inline_schema_aggregator.add(property_schema_id, schema)
                    else:
                        property_schema_id = f"<inline+{models.SchemaObject.__name__}>"
                        schema = self.parse_item(property_schema_id, property_schema_data)

                description = property_schema_data.get("description", "")
                match = re.search(r"(__safety_key__)\((?P<safety_key>.+)\)", description)
                safety_key = match["safety_key"] if match else None

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
                        orig_key="text",
                        safety_key=None,
                        schema=models.SchemaObject(
                            id="",
                            type=models.Type.string,
                            enum=None,
                            properties=[],
                            title=None,
                            format=None,
                            items=None,
                            required=[],
                        ),
                    )
                )
            if schema_type == models.Type.string and data_format == models.Format.binary:
                properties.append(
                    models.SchemaProperty(
                        orig_key="content",
                        safety_key=None,
                        schema=models.SchemaObject(
                            id="",
                            type=models.Type.string,
                            enum=None,
                            properties=[],
                            title=None,
                            format=models.Format.binary,
                            items=None,
                            required=[],
                        ),
                    )
                )

            if schema_type == models.Type.integer:
                properties.append(
                    models.SchemaProperty(
                        orig_key="text",
                        safety_key=None,
                        schema=models.SchemaObject(
                            id="",
                            type=models.Type.integer,
                            enum=None,
                            properties=[],
                            title=None,
                            format=None,
                            items=None,
                            required=[],
                        ),
                    )
                )

        return properties

    def _parse_items(
        self,
        parent_schema_id: str,
        data: dict[str, Any],
    ) -> models.SchemaObject | list[models.SchemaObject] | None:
        items_schema_data = data.get("items")
        if items_schema_data:
            if items_schema_data.get("$ref", None):
                resolved_ref = self._ref_resolver.resolve(items_schema_data["$ref"])
                schema = self.parse_item(resolved_ref.ref_id, resolved_ref.ref_data, from_depth_level=True)
                return schema
            else:
                parent_raw_type = data.get("type")
                if parent_raw_type == "array":
                    items_schema_id = f"{parent_schema_id}Item"
                else:
                    items_schema_id = f"<inline+{models.SchemaObject.__name__}>"
                schema = self.parse_item(items_schema_id, items_schema_data)
                items_schema_data_type = items_schema_data.get("type")

                if items_schema_data_type and not models.Type(items_schema_data_type).is_primitive:
                    self._inline_schema_aggregator.add(items_schema_id, schema)

                return schema

        return None
