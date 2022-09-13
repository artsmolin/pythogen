"""
Responsible for rendering/generating client code from data
that was parsed from an OpenAPI file.
"""


import logging
from dataclasses import dataclass
from typing import Dict
from typing import Generic
from typing import List
from typing import Tuple
from typing import TypeVar

import inflection
from jinja2 import Environment
from jinja2 import FileSystemLoader

from pythogen import models
from pythogen import settings


PathStr = TypeVar('PathStr', bound=str)


logger = logging.getLogger(__name__)


def render_client(*, output_path: str, document: models.Document, name: str, sync: bool, metrics: bool) -> None:
    """Отрисовывает сгенерированный клиент на основе j2-шаблонов

    Arguments
    ---------
    output_path
        Пудо до файла, в который запишется сгенерированный клиент
    document
        Спаршенный в python-объекты OpenApi-файл
    """
    env = Environment(loader=FileSystemLoader(settings.TEMPLATES_DIR_PATH), extensions=['jinja2.ext.loopcontrols'])
    template = env.get_template(
        settings.CLIENT_TEMPLATE_NAME,
        globals={
            'varname': varname,
            'classname': classname,
            'typerepr': j2_typerepr,
            'responserepr': j2_responserepr,
            'iterresponsemap': iterresponsemap,
        },
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
        metrics=metrics,
        discriminator_base_class_schemas=document.discriminator_base_class_schemas,
    )
    with open(output_path, 'w') as output_file:
        output_file.write(rendered_client)


@dataclass
class PreparedOperations(Generic[PathStr]):
    get: Dict[PathStr, models.OperationObject]
    post: Dict[PathStr, models.OperationObject]
    post_no_body: Dict[PathStr, models.OperationObject]
    put: Dict[PathStr, models.OperationObject]
    patch: Dict[PathStr, models.OperationObject]
    delete_no_body: Dict[PathStr, models.OperationObject]


def prepare_operations(document: models.Document) -> PreparedOperations:
    prepared_operations: PreparedOperations = PreparedOperations(
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


def iterresponsemap(responses: models.ResponsesObject) -> List[Tuple[str, str]]:
    mapping = []

    for code, response in responses.patterned.items():
        if response.schema is None:
            mapper = 'EmptyBody(status_code=response.status_code, text=response.text)'
            mapping.append((code, mapper))
            continue

        if response.schema.type == models.Type.object:
            mapper = f'{classname(response.schema.id)}.parse_obj(response.json())'
            mapping.append((code, mapper))
            continue

        if response.schema.type == models.Type.any_of and isinstance(response.schema.items, list):
            items_class_names = [classname(items.id) for items in response.schema.items]
            items_class_names_str: str = '[' + ', '.join(items_class_names) + ']'
            mapper = f'self._parse_any_of(response.json(), {items_class_names_str})'
            mapping.append((code, mapper))
            continue

        if response.schema.type is models.Type.array and response.schema.items:
            if isinstance(response.schema.items, list):
                items_collection = response.schema.items
            else:
                items_collection = [response.schema.items]

            for items in items_collection:
                if items.type is models.Type.object:
                    items_class_name = classname(items.id)
                    mapper = f'[{items_class_name}.parse_obj(item) for item in response.json()]'
                    mapping.append((code, mapper))
                    continue

                mapper = f'response.json()'
                mapping.append((code, mapper))
                continue
            continue

        if response.schema.type == models.Type.string:
            if response.schema.format is models.Format.binary:
                mapper = f'{classname(response.schema.id)}(content=response.content)'
                mapping.append((code, mapper))
                continue

            mapper = f'{classname(response.schema.id)}(text=response.text)'
            mapping.append((code, mapper))
            continue

        raise NotImplementedError(
            f'Unable to create response mapping of {response.id} <response.schema.type={response.schema.type}>'
        )

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

    representation = 'Dict'

    if schema.type in primitive_type_mapping:
        if schema.enum:
            representation = f'Literal{schema.enum}'
        elif schema.format in format_mapping:
            representation = format_mapping[schema.format]  # type: ignore
        else:
            representation = primitive_type_mapping[schema.type]

    elif schema.type == models.Type.object and schema.id != '<inline+SchemaObject>':
        representation = classname(schema.id)

    elif schema.type == models.Type.array and schema.items:
        if schema.items.type is models.Type.any_of:  # type: ignore
            items = [classname(item.id) for item in schema.items.items]  # type: ignore
            representation = f'List[Union{items}]'
        else:
            item = j2_typerepr(schema.items)  # type: ignore
            representation = f'List[{item}]'

    elif schema.type == models.Type.any_of:
        representation = classname(schema.id)

    return representation


def varname(value: str) -> str:
    return inflection.underscore(value)


def classname(value: str) -> str:
    value = value.replace('.', '')
    return inflection.camelize(value)
