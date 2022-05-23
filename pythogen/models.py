"""
Models for parsing OpenApi specifications (https://swagger.io/specification/#oas-document)
"""

from __future__ import annotations

import keyword
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


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

    name: Optional[str]
    url: Optional[str]
    email: Optional[str]


@dataclass
class LicenseObject:
    """
    https://swagger.io/specification/#license-object
    """

    name: str
    url: Optional[str]


@dataclass
class InfoObject:
    """
    https://swagger.io/specification/#info-object
    """

    title: str
    version: str
    description: Optional[str] = None
    termsOfService: Optional[str] = None
    contact: Optional[ContactObject] = None
    license: Optional[LicenseObject] = None


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
    safety_key: Optional[str]
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
    title: Optional[str]
    required: Optional[list[str]]
    enum: list[str]
    type: Type
    format: Optional[str]
    items: Optional['SchemaObject']
    properties: list[SchemaProperty]
    description: Optional[str] = None

    # Технические поля
    discriminator_base_class_schema: Optional[DiscriminatorBaseClassSchema] = None

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
    safety_key: Optional[str]
    description: Optional[str]
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
    description: Optional[str]
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
    summary: Optional[str]
    description: Optional[str]
    operation_id: Optional[str]
    request_body: Optional[RequestBodyObject]
    responses: ResponsesObject
    parameters: list[ParameterObject]

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
    def fn_name(self) -> str:
        value = self.operation_id.replace('-', '_')
        return value


@dataclass
class PathItemObject:
    """
    https://swagger.io/specification/#path-item-object
    """

    summary: Optional[str]
    description: Optional[str]
    operations: dict[HttpMethod, OperationObject]


@dataclass
class ResponseObject:
    id: str
    description: str
    schema: Optional[SchemaObject]


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

    @property
    def sorted_schemas(self) -> list[SchemaObject]:
        sorted = []
        keys = list(self.schemas.keys())
        while keys:
            key = keys.pop()
            if key in sorted:
                index = sorted.index(key)
            else:
                sorted.append(key)
                index = len(sorted) - 1

            schema = self.schemas[key]
            for property in schema.properties:
                if property.schema.id in self.schemas and property.schema.id not in sorted:
                    sorted.insert(index, property.schema.id)
                if property.schema.items and property.schema.items.id in self.schemas:
                    sorted.insert(index, property.schema.items.id)

        sorted_schemas = []
        for key in sorted:
            if self.schemas[key] not in sorted_schemas:
                sorted_schemas.append(self.schemas[key])
        return sorted_schemas


@dataclass
class DiscriminatorBaseClassSchema:
    name: str
    attr: str
