"""
Models for parsing OpenApi specifications (https://swagger.io/specification/#oas-document)
"""

from __future__ import annotations

import keyword
import re
from dataclasses import dataclass
from dataclasses import field
from enum import Enum


class SafetyKeyMixin:
    pydantic_reserved_properties = ("schema",)

    @property
    def key(self):
        return self._safe_key()

    def _safe_key(self):
        if self.safety_key:
            return self.safety_key

        if all(
            (
                self.orig_key.isidentifier(),
                not keyword.iskeyword(self.orig_key),
                self.orig_key not in self.pydantic_reserved_properties,
            )
        ):
            return self.orig_key

        key = self.orig_key

        if not key.isidentifier():
            key = re.sub("[-.]", "_", key)
            # stolen from https://stackoverflow.com/a/3303361
            key = re.sub("[^0-9a-zA-Z_]", "", key)
            key = re.sub("^[^a-zA-Z_]+", "", key)

        if keyword.iskeyword(key):
            key += "_"

        if key in self.pydantic_reserved_properties:
            key += "_"

        self.safety_key = key
        return self.safety_key


class HttpMethod(Enum):
    get = "get"
    put = "put"
    post = "post"
    delete = "delete"
    options = "options"
    head = "head"
    patch = "patch"
    trace = "trace"


class ParameterLocation(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


class Format(Enum):
    int32 = "int32"
    int64 = "int64"
    float = "float"
    double = "double"
    date = "date"
    byte = "byte"
    binary = "binary"
    datetime = "date-time"
    password = "password"
    uuid = "uuid"
    uri = "uri"
    hostname = "hostname"
    ipv4 = "ipv4"
    ipv6 = "ipv6"
    ipvanyaddress = "ipvanyaddress"

    @classmethod
    def _missing_(cls, value):
        value = re.sub("[_-]*", "", value)
        for member in cls:
            if member.name.lower() == value:
                return member
        return None


@dataclass
class ContactObject:
    """
    https://swagger.io/specification/#contact-object
    """

    name: str | None
    url: str | None
    email: str | None


@dataclass
class LicenseObject:
    """
    https://swagger.io/specification/#license-object
    """

    name: str
    url: str | None


@dataclass
class InfoObject:
    """
    https://swagger.io/specification/#info-object
    """

    title: str
    version: str
    description: str | None = None
    termsOfService: str | None = None
    contact: ContactObject | None = None
    license: LicenseObject | None = None


class Type(Enum):
    string = "string"
    number = "number"
    integer = "integer"
    boolean = "boolean"
    array = "array"
    object = "object"
    null = "null"

    @property
    def is_primitive(self) -> bool:
        return self in (
            Type.string,
            Type.number,
            Type.integer,
            Type.boolean,
            Type.null,
        )


@dataclass
class SchemaProperty(SafetyKeyMixin):
    orig_key: str
    safety_key: str | None
    schema: "SchemaObject"


@dataclass
class SchemaObject:
    """
    https://swagger.io/specification/#schema-object
    """

    id: str
    title: str | None
    enum: list[str] | None
    type: Type
    format: Format | None
    items: "SchemaObject" | list["SchemaObject"] | None
    properties: list[SchemaProperty]
    description: str | None = None
    additional_roperties: bool = False
    required: list[str] = field(default_factory=list)
    all_of: list["SchemaObject"] = field(default_factory=list)
    any_of: list["SchemaObject"] = field(default_factory=list)
    discriminator: Discriminator | None = None

    # numbers
    minimum: int | None = None
    maximum: int | None = None
    exclusive_minimum: bool = False
    exclusive_maximum: bool = False

    # Технические поля
    discriminator_base_class_schema: DiscriminatorBaseClassSchema | None = None
    is_fake: bool = False
    is_inline: bool = False

    @property
    def required_properties(self) -> list[SchemaProperty]:
        if not self.required:
            return []

        return [p for p in self.properties if p.orig_key in self.required]

    @property
    def optional_properties(self) -> list[SchemaProperty]:
        if not self.required:
            return self.properties

        return [p for p in self.properties if p.orig_key not in self.required]

    @property
    def inline_allof_models(self) -> list[SchemaObject]:
        return [item for item in self.all_of if item.is_inline]

    @property
    def named_allof_models(self) -> list[SchemaObject]:
        return [item for item in self.all_of if not item.is_inline]

    @property
    def is_empty_object(self) -> bool:
        return all(
            (
                self.type is Type.object,
                not self.is_fake,
                not self.enum,
                not self.items,
                not self.properties,
                not self.required,
                not self.all_of,
                not self.any_of,
                not self.discriminator,
            )
        )


@dataclass
class ParameterObject(SafetyKeyMixin):
    """
    https://swagger.io/specification/#parameter-object
    """

    id: str
    orig_key: str
    safety_key: str | None
    description: str | None
    location: ParameterLocation
    required: bool
    schema: SchemaObject


@dataclass
class RequestBodyObject:
    """
    https://swagger.io/specification/#request-body-object
    """

    id: str
    description: str | None
    schema: SchemaObject
    required: bool
    is_form_data: bool
    is_multipart_form_data: bool
    are_files_required: bool


@dataclass
class OperationObject:
    """
    https://swagger.io/specification/#operation-object
    """

    method: HttpMethod
    summary: str | None
    description: str | None
    operation_id: str | None
    request_body: RequestBodyObject | None
    responses: ResponsesObject
    parameters: list[ParameterObject]
    path_str: str

    @property
    def path_params(self) -> list[ParameterObject]:
        return [parameter for parameter in self.parameters if parameter.location == ParameterLocation.path]

    @property
    def query_params(self) -> list[ParameterObject]:
        return [parameter for parameter in self.parameters if parameter.location == ParameterLocation.query]

    @property
    def headers(self) -> list[ParameterObject]:
        return [parameter for parameter in self.parameters if parameter.location == ParameterLocation.header]

    @property
    def fn_name(self) -> str | None:
        if self.operation_id is not None:
            return self.operation_id.replace("-", "_")

        name = self.path_str.removeprefix("/").replace("-", "_").replace("/", "_").replace("{", "").replace("}", "")
        name = self.method.value + "_" + name
        name = name.lower()
        return name


@dataclass
class PathItemObject:
    """
    https://swagger.io/specification/#path-item-object
    """

    summary: str | None
    description: str | None
    operations: dict[HttpMethod, OperationObject]


@dataclass
class ResponseObject:
    id: str
    description: str
    schema: SchemaObject | None


@dataclass
class ResponsesObject:
    patterned: dict[str, ResponseObject]


@dataclass
class Document:
    info: InfoObject
    paths: dict[str, PathItemObject]
    parameters: dict[str, ParameterObject]
    schemas: dict[str, SchemaObject]

    discriminator_base_class_schemas: list[DiscriminatorBaseClassSchema]

    def _build_sorted_schemas(self, keys: list[str], exclude_enums: bool = False):
        sorted: list[str] = []
        key_for_processing = set(keys)
        while keys:
            key = keys.pop()
            if key in sorted:
                index = sorted.index(key)
            else:
                sorted.append(key)
                index = len(sorted) - 1

            schema = self.schemas[key]

            for all_of_item in schema.all_of:
                if all_of_item.id in key_for_processing and all_of_item.id not in sorted:
                    sorted.insert(index, all_of_item.id)

            for property in schema.properties:
                if property.schema.id in key_for_processing and property.schema.id not in sorted:
                    sorted.insert(index, property.schema.id)
                if property.schema.items:
                    if isinstance(property.schema.items, list):
                        for items in property.schema.items:
                            if items.id in self.schemas:
                                sorted.insert(index, items.id)
                    elif property.schema.items.id in self.schemas:
                        sorted.insert(index, property.schema.items.id)

        sorted_schemas = []
        for key in sorted:
            if self.schemas[key] not in sorted_schemas:
                sorted_schemas.append(self.schemas[key])

        if exclude_enums:
            sorted_schemas = [s for s in sorted_schemas if s.enum is None]

        return sorted_schemas

    @property
    def sorted_schemas(self) -> list[SchemaObject]:
        keys = [key for key, schema in self.schemas.items() if schema.enum is None and not schema.type.is_primitive]
        return self._build_sorted_schemas(keys, exclude_enums=True)

    @property
    def sorted_enums(self) -> list[SchemaObject]:
        keys = [key for key, schema in self.schemas.items() if schema.enum is not None]
        return self._build_sorted_schemas(keys)


@dataclass
class DiscriminatorBaseClassSchema:
    name: str
    attr: str


@dataclass
class Discriminator:
    property_name: str
    mapping: dict[str, SchemaObject]
