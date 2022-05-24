"""
Responsible for rendering/generating client code from data
that was parsed from an OpenAPI file.
"""


import logging
from dataclasses import dataclass
from typing import TypeVar

import inflection
from jinja2 import Environment
from jinja2 import FileSystemLoader

from pythogen import models
from pythogen import settings


PathStr = TypeVar('PathStr', bound=str)


logger = logging.getLogger(__name__)


def render_client(*, output_path: str, document: models.Document, name, sync) -> None:
    """Отрисовывает сгенерированный клиент на основе j2-шаблонов

    Arguments
    ---------
    output_path
        Пудо до файла, в который запишется сгенерированный клиент
    document
        Спаршенный в python-объекты OpenApi-файл
    """
    env = Environment(loader=FileSystemLoader(settings.TEMPLATES_DIR_PATH), extensions=['jinja2.ext.loopcontrols'])
    template = env.get_template(settings.CLIENT_TEMPLATE_NAME)
    template.globals.update(
        {
            'varname': varname,
            'classname': classname,
            'typerepr': j2_typerepr,
            'responserepr': j2_responserepr,
            'iterresponsemap': iterresponsemap,
        }
    )

    prepared_operations = prepare_operations(document)

    rendered_client = template.render(
        name=name,
        version=document.info.version,
        models=document.sorted_schemas,
        get=prepared_operations.get,
        post=prepared_operations.post,
        patch=prepared_operations.patch,
        post_no_body=prepared_operations.post_no_body,
        put=prepared_operations.put,
        delete_no_body=prepared_operations.delete_no_body,
        sync=sync,
        discriminator_base_class_schemas=document.discriminator_base_class_schemas,
    )
    with open(output_path, 'w') as output_file:
        output_file.write(rendered_client)


@dataclass
class PreparedOperations:
    get: dict[PathStr, models.OperationObject]
    post: dict[PathStr, models.OperationObject]
    post_no_body: dict[PathStr, models.OperationObject]
    put: dict[PathStr, models.OperationObject]
    patch: dict[PathStr, models.OperationObject]
    delete_no_body: dict[PathStr, models.OperationObject]


def prepare_operations(document: models.Document) -> PreparedOperations:
    prepared_operations = PreparedOperations(
        get={},
        post={},
        post_no_body={},
        put={},
        patch={},
        delete_no_body={},
    )

    for path, path_item in document.paths.items():
        for method, operation in path_item.operations.items():
            if method is models.HttpMethod.get:
                prepared_operations.get[path] = operation
            elif method is models.HttpMethod.post:
                prepared_operations.post[path] = operation
            elif method is models.HttpMethod.patch:
                prepared_operations.patch[path] = operation
            elif method is models.HttpMethod.put:
                prepared_operations.put[path] = operation
            elif method is models.HttpMethod.delete:
                prepared_operations.delete_no_body[path] = operation
            else:
                logger.error(f'Unable to parse document, "{method}" operations support not implemented yet')

    return prepared_operations


def iterresponsemap(responses: models.ResponsesObject) -> list[tuple[str, str]]:
    mapping = []

    for code, response in responses.patterned.items():
        if response.schema is None:
            mapper = 'EmptyBody(status_code=response.status_code, text=response.text)'
        else:
            if response.schema.type == models.Type.object:
                mapper = f'{classname(response.schema.id)}.parse_obj(response.json())'

            elif response.schema.type is models.Type.array:
                if response.schema.items.type is models.Type.object:
                    items_class_name = classname(response.schema.items.id)
                    mapper = f'[{items_class_name}.parse_obj(item) for item in response.json()]'
                else:
                    mapper = f'response.json()'

            elif response.schema.type == models.Type.string:
                if response.schema.format is models.Format.binary:
                    mapper = f'{classname(response.schema.id)}(content=response.content)'
                else:
                    mapper = f'{classname(response.schema.id)}(text=response.text)'
            else:
                raise NotImplementedError(f'Unable to create response mapping of {response.id}')
        mapping.append((code, mapper))

    return mapping


def j2_responserepr(responses: models.ResponsesObject) -> str:
    """Represent method response on j2 template"""
    # print(responses)
    types = []

    for response in responses.patterned.values():
        if not response.schema:
            types.append('EmptyBody')
        elif response.schema.type != models.Type.string:
            types.append(j2_typerepr(response.schema))
        else:
            types.append(classname(response.schema.id))

    if not types:
        return 'None'
    elif len(types) == 1:
        return f'Optional[{types[0]}]'
    else:
        union_args = ', '.join(types)
        return f'Union[{union_args}]'


def j2_typerepr(schema: models.SchemaObject) -> str:
    """Represent data type on j2 template"""
    primitive_type_mapping = {
        models.Type.integer: 'int',
        models.Type.number: 'float',
        models.Type.boolean: 'bool',
        models.Type.string: 'str',
    }
    format_mapping = {
        models.Format.binary: 'bytes',
        models.Format.uri: 'HttpUrl',
        models.Format.date: 'date',
        models.Format.date_time: 'datetime',
    }

    representation = 'dict'

    if schema.type in primitive_type_mapping:
        if schema.enum:
            representation = f'Literal{schema.enum}'
        elif schema.format in format_mapping:
            representation = format_mapping[schema.format]  # type: ignore
        else:
            representation = primitive_type_mapping[schema.type]

    if schema.type == models.Type.object and schema.id != '<inline+SchemaObject>':
        representation = classname(schema.id)

    elif schema.type == models.Type.array:
        if schema.items.type is models.Type.any_of:
            items = [classname(item.schema.id) for item in schema.items.items]  # type: ignore
            representation = f'list[Union{items}]'
        else:
            items = j2_typerepr(schema.items)
            representation = f'list[{items}]'

    elif schema.type == models.Type.any_of:
        representation = classname(schema.id)

    return representation


def varname(value: str) -> str:
    return inflection.underscore(value)


def classname(value: str) -> str:
    value = value.replace('.', '')
    return inflection.camelize(value)
