"""
Responsible for rendering/generating client code from data
that was parsed from an OpenAPI file.
"""
import logging
import re
from dataclasses import dataclass
from typing import Generic
from typing import TypeVar

import autoflake
import black
import inflection
import isort
from jinja2 import Environment
from jinja2 import FileSystemLoader

from pythogen import models
from pythogen import settings


PathStr = TypeVar("PathStr", bound=str)


logger = logging.getLogger(__name__)


def render_client(
    *,
    output_path: str,
    document: models.Document,
    name: str,
    sync: bool,
    metrics: bool,
    pythogen_version: str,
    required_headers: list[str] | None = None,
) -> None:
    """Отрисовывает сгенерированный клиент на основе j2-шаблонов

    Arguments
    ---------
    output_path
        Пудо до файла, в который запишется сгенерированный клиент
    document
        Спаршенный в python-объекты OpenApi-файл
    """
    env = Environment(
        loader=FileSystemLoader(settings.HTTP_CLIENT_TEMPLATES_DIR_PATH), extensions=["jinja2.ext.loopcontrols"]
    )
    template = env.get_template(
        settings.CLIENT_TEMPLATE_NAME,
        globals={
            "varname": varname,
            "classname": classname,
            "typerepr": j2_typerepr,
            "responserepr": j2_responserepr,
            "iterresponsemap": iterresponsemap,
            "parameterfield": parameterfield,
            "propertyfield": propertyfield,
            "repranyof": j2_repr_any_of,
        },
    )

    prepared_operations = prepare_operations(document)

    rendered_client = template.render(
        document=document,
        name=name,
        version=document.info.version,
        enums=document.sorted_enums,
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
        required_headers=required_headers,
        operations=prepared_operations.all(),
        pythogen_version=pythogen_version,
    )
    rendered_client = black.format_str(rendered_client, mode=black.Mode(line_length=120))
    rendered_client = isort.code(
        rendered_client,
        force_grid_wrap=2,
        lines_after_imports=2,
        force_single_line=True,
        line_length=120,
    )
    rendered_client = autoflake.fix_code(
        rendered_client,
        remove_all_unused_imports=True,
    )
    with open(output_path, "w") as output_file:
        output_file.write(rendered_client)


@dataclass
class PreparedOperations(Generic[PathStr]):
    get: dict[PathStr, models.OperationObject]
    post: dict[PathStr, models.OperationObject]
    post_no_body: dict[PathStr, models.OperationObject]
    put: dict[PathStr, models.OperationObject]
    patch: dict[PathStr, models.OperationObject]
    delete_no_body: dict[PathStr, models.OperationObject]

    def all(self) -> tuple[models.OperationObject, ...]:
        return (
            *self.get.values(),
            *self.post.values(),
            *self.post_no_body.values(),
            *self.put.values(),
            *self.patch.values(),
            *self.delete_no_body.values(),
        )


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


def iterresponsemap(responses: models.ResponsesObject) -> list[tuple[str, str]]:
    mapping = []

    for code, response in responses.patterned.items():
        if response.schema is None:
            mapper = "EmptyBody(status_code=response.status_code, text=response.text)"
            mapping.append((code, mapper))
            continue

        if response.schema.type == models.Type.object and response.schema.is_empty_object:
            mapper = "response.json()"
            mapping.append((code, mapper))
            continue

        if response.schema.type == models.Type.object:
            mapper = f"{classname(response.schema.id)}.model_validate(response.json())"
            mapping.append((code, mapper))
            continue

        if response.schema.any_of:
            items_class_names = [classname(items.id) for items in response.schema.any_of]
            items_class_names_str: str = "[" + ", ".join(items_class_names) + "]"
            mapper = f"self._parse_any_of(response.json(), {items_class_names_str})"
            mapping.append((code, mapper))
            continue

        if response.schema.type == models.Type.array:
            if isinstance(response.schema.items, list):
                items_collection = response.schema.items
            else:
                items_collection = [response.schema.items]  # type: ignore

            for items in items_collection:
                if items is None:
                    mapper = "EmptyBody(status_code=response.status_code, text=response.text)"
                    mapping.append((code, mapper))
                    continue

                if items.type is models.Type.object:
                    items_class_name = classname(items.id)
                    mapper = f"[{items_class_name}.model_validate(item) for item in response.json()]"
                    mapping.append((code, mapper))
                    continue

                mapper = "response.json()"
                mapping.append((code, mapper))
                continue
            continue

        if response.schema.type == models.Type.string and response.schema.format is models.Format.binary:
            mapping.append((code, "response.content"))
            continue

        if response.schema.type == models.Type.string:
            mapping.append((code, "response.text"))
            continue

        if response.schema.type == models.Type.integer:
            mapping.append((code, "int(response.text)"))
            continue

        raise NotImplementedError(
            f"Unable to create response mapping of {response.id} <response.schema.type={response.schema.type}>"
        )

    return mapping


def j2_responserepr(responses: models.ResponsesObject, document: models.Document) -> str:
    """Represent method response on j2 template"""
    types = []

    for response in responses.patterned.values():
        if not response.schema:
            types.append("EmptyBody")
        else:
            types.append(j2_typerepr(response.schema, document))

    types = sorted(set(types))

    if not types:
        return "None"

    elif len(types) == 1:
        return f"{types[0]} | None"
    else:
        return " | ".join(types)


def j2_typerepr(schema: models.SchemaObject, document: models.Document) -> str:
    """Represent data type on j2 template"""
    schema = document.schemas.get(schema.id, schema)

    representation = "dict"

    if schema.type.is_primitive:
        if schema.enum:
            if schema.id == "<inline+SchemaObject>":
                representation = f"Literal{schema.enum}"
            else:
                representation = classname(schema.id)
        elif schema.format in FORMAT_MAPPING:
            representation = FORMAT_MAPPING[schema.format]  # type: ignore
        else:
            representation = PRIMITIVE_TYPE_MAPPING[schema.type]

    elif schema.type == models.Type.object and schema.id != "<inline+SchemaObject>":
        if schema.is_empty_object:
            representation = "dict[Any, Any]"
        else:
            representation = classname(schema.id)

    elif schema.any_of:
        representation = classname(schema.id)

    elif (
        schema.type == models.Type.array
        and schema.items
        and isinstance(schema.items, models.SchemaObject)
        and schema.items.any_of
    ):
        represented_items = " | ".join((j2_typerepr(anyof_item, document) for anyof_item in schema.items.any_of))
        representation = f"list[{represented_items}]"

    elif schema.type == models.Type.array and schema.items:
        represented_item = j2_typerepr(schema.items, document)  # type: ignore
        representation = f"list[{represented_item}]"

    elif schema.discriminator:
        representation = " | ".join((j2_typerepr(item, document) for item in schema.discriminator.mapping.values()))

    if schema.all_of and len(schema.all_of) == 1:
        representation = j2_typerepr(schema.all_of[0], document)

    return representation


def j2_repr_any_of(any_of_items: list[models.SchemaObject], document: models.Document) -> str:
    items = []
    for item in any_of_items:
        if item.additional_roperties:
            items.append("dict[Any, Any]")
        elif item.type is models.Type.array and item.items:
            repr = j2_typerepr(item, document)
            items.append(repr)
        elif item.type.is_primitive:
            items.append(PRIMITIVE_TYPE_MAPPING[item.type])
        elif item.is_empty_object:
            items.append("dict[Any, Any]")
        elif item.id:
            items.append(classname(item.id))
        else:
            logger.error(f"j2_repr_any_of unsupported SchemaObject {item}")
    return " | ".join(items)


def varname(value: str) -> str:
    clean_value = re.sub(r"\W|^(?=\d)", "_", value)  # remove special characters
    clean_value = re.sub("_{2,}", "_", clean_value)  # __ -> _
    clean_value = clean_value.replace(" ", "_")
    return inflection.underscore(clean_value)


def classname(value: str) -> str:
    clean_value = re.sub(r"\W|^(?=\d)", "_", value)  # remove special characters
    clean_value = re.sub("_{2,}", "_", clean_value)  # __ -> _
    return inflection.camelize(clean_value)


def parameterfield(parameter: models.ParameterObject) -> str:
    args: list[str] = []

    if not parameter.required:
        args.append("None")

    if parameter.safety_key != parameter.orig_key:
        args.append(f'alias="{parameter.orig_key}"')

    if parameter.description:
        args.append(f'description="{parameter.description}"')

    if parameter.schema.discriminator:
        args.append(f'discriminator="{parameter.schema.discriminator.property_name}"')

    return "Field(" + ", ".join(args) + ")"


def propertyfield(property: models.SchemaProperty, parent_schema: models.SchemaObject) -> str:
    args: list[str] = []

    if property.orig_key not in parent_schema.required:
        args.append("None")
    else:
        args.append("...")

    if property.schema.minimum is not None:
        if property.schema.exclusive_minimum:
            args.append(f"gt={property.schema.minimum}")
        else:
            args.append(f"ge={property.schema.minimum}")

    if property.schema.maximum is not None:
        if property.schema.exclusive_maximum:
            args.append(f"lt={property.schema.maximum}")
        else:
            args.append(f"le={property.schema.maximum}")

    if property.safety_key and property.safety_key != property.orig_key:
        args.append(f'alias="{property.orig_key}"')

    if not property.safety_key and varname(property.orig_key) != property.orig_key:
        args.append(f'alias="{property.orig_key}"')

    if property.schema.description:
        args.append(f'description="{property.schema.description}"')

    if property.schema.discriminator:
        args.append(f'discriminator="{property.schema.discriminator.property_name}"')

    if args == ["None"]:
        return "= None"

    if args == ["..."]:
        return ""

    return "= Field(" + ", ".join(args) + ")"


PRIMITIVE_TYPE_MAPPING = {
    models.Type.integer: "int",
    models.Type.number: "float",
    models.Type.boolean: "bool",
    models.Type.string: "str",
    models.Type.null: "None",
}

FORMAT_MAPPING = {
    models.Format.binary: "bytes",
    models.Format.uri: "HttpUrl",
    models.Format.date: "datetime.date",
    models.Format.datetime: "datetime.datetime",
}
