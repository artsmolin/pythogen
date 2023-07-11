"""
Models for parsing OpenApi specifications (https://swagger.io/specification/#oas-document)
"""

from __future__ import annotations

import keyword
import re
from dataclasses import dataclass
from enum import Enum


class HttpMethod(Enum):
    get = 'get'
    put = 'put'
    post = 'post'
    delete = 'delete'
    options = 'options'
    head = 'head'
    patch = 'patch'
    trace = 'trace'


class ParameterLocation(Enum):
    query = 'query'
    header = 'header'
    path = 'path'
    cookie = 'cookie'


class Format(Enum):
    int32 = 'int32'
    int64 = 'int64'
    float = 'float'
    double = 'double'
    date = 'date'
    byte = 'byte'
    binary = 'binary'
    date_time = 'date-time'
    password = 'password'
    uuid = 'uuid'
    uri = 'uri'


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
    string = 'string'
    number = 'number'
    integer = 'integer'
    boolean = 'boolean'
    array = 'array'
    object = 'object'

    # TODO: refactor
    any_of = 'any_of'


@dataclass
class SchemaProperty:
    orig_key: str
    safety_key: str | None
    schema: 'SchemaObject'

    @property
    def key(self):
        return self._safe_key()

    def _safe_key(self):
        if self.safety_key:
            return self.safety_key

        if self.orig_key.isidentifier() and not keyword.iskeyword(self.orig_key):
            return self.orig_key

        key = self.orig_key

        if not key.isidentifier():
            key = re.sub('[-.]', '_', key)
            # stolen from https://stackoverflow.com/a/3303361
            key = re.sub('[^0-9a-zA-Z_]', '', key)
            key = re.sub('^[^a-zA-Z_]+', '', key)

        if keyword.iskeyword(key):
            key += "_"

        self.safety_key = key
        return self.safety_key


@dataclass
class SchemaObject:
    """
    https://swagger.io/specification/#schema-object
    """

    id: str
    title: str | None
    required: list[str] | None
    enum: list[str] | None
    type: Type
    format: Format | None
    items: 'SchemaObject' | list['SchemaObject'] | None
    properties: list[SchemaProperty]
    description: str | None = None

    # Технические поля
    discriminator_base_class_schema: DiscriminatorBaseClassSchema | None = None
    is_fake: bool = False

    @property
    def required_properties(self) -> list[SchemaProperty]:
        if self.required is None:
            return []

        return [p for p in self.properties if p.orig_key in self.required]

    @property
    def optional_properties(self) -> list[SchemaProperty]:
        if self.required is None:
            return self.properties

        return [p for p in self.properties if p.orig_key not in self.required]


@dataclass
class ParameterObject:
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

    @property
    def key(self):
        return self.safety_key if self.safety_key else self.orig_key


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
            return self.operation_id.replace('-', '_')

        name = self.path_str.removeprefix('/').replace('-', '_').replace('/', '_').replace('{', '').replace('}', '')
        name = self.method.value + '_' + name
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

    def _build_sorted_schemas(self, keys):
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
        return sorted_schemas

    @property
    def sorted_schemas(self) -> list[SchemaObject]:
        schema_keys = list(filter(lambda x: self.schemas[x].enum is None, self.schemas.keys()))
        return self._build_sorted_schemas(schema_keys)

    @property
    def sorted_enums(self) -> list[SchemaObject]:
        enum_keys = list(filter(lambda x: self.schemas[x].enum is not None, self.schemas.keys()))
        return self._build_sorted_schemas(enum_keys)


@dataclass
class DiscriminatorBaseClassSchema:
    name: str
    attr: str
