import logging
from typing import Any
from typing import Dict

from pythogen import models
from pythogen.parsers import constants
from pythogen.parsers.references import RefResolver
from pythogen.parsers.schemas import SchemaParser


logger = logging.getLogger(__name__)


class RequestBodyParser:
    def __init__(self, ref_resolver: RefResolver, schema_parser: SchemaParser) -> None:
        self._ref_resolver = ref_resolver
        self._schema_parser = schema_parser

    def parse_item(self, request_body_data: Dict[str, Any]) -> models.RequestBodyObject:
        """Спарсить спецификацию тела ручки"""
        if request_body_data.get('$ref', None):
            resolved_ref = self._ref_resolver.resolve(request_body_data['$ref'])
            data = resolved_ref.ref_data
            id_ = resolved_ref.ref_id
        else:
            data = request_body_data
            id_ = f'<inline+{models.RequestBodyObject.__name__}>'

        files_required = False
        content = data.get('content')
        if content:
            media_types = list(content.keys())
            if len(media_types) > 1:
                logger.error(f'Unable to parse request body "{id_}", multiple media types not implemented yet')
            media_type = media_types[0]
            media_type_data = content[media_type]
            schema_data = media_type_data['schema']
            if schema_data.get('$ref', None):
                resolved_ref = self._ref_resolver.resolve(schema_data['$ref'])
                schema = self._schema_parser.parse_item(resolved_ref.ref_id, resolved_ref.ref_data)
            else:
                schema = self._schema_parser.parse_item(f'<inline+{models.SchemaObject.__name__}>', schema_data)

            if media_type == constants.MULTIPART_FORM_DATA_TYPE:
                files_required = self._drop_binary_strings(schema_data)
        else:
            raise Exception(f'Unable to parse request body "{id_}", field "content" must be specified')

        type_schema_dict_keys = data.get('content', {}).keys()
        type_schema = list(type_schema_dict_keys)[0] if len(type_schema_dict_keys) else ''
        return models.RequestBodyObject(
            id=id_,
            description=data.get('description'),
            schema=schema,
            required=data.get('required', False),
            is_form_data=type_schema == constants.FORM_DATA_TYPE,
            is_multipart_form_data=type_schema == constants.MULTIPART_FORM_DATA_TYPE,
            are_files_required=files_required,
        )

    @staticmethod
    def _drop_binary_strings(schema_data):
        """
        drop from request schema file-related properties
        """
        properties = schema_data.get("properties", {})
        required = schema_data.get("required", [])
        file_required = False
        for k in list(schema_data.get("properties", {})):
            prop = properties[k]
            if prop.get("type") == "string" and prop.get("format") == models.DataFormat.binary.value:
                del properties[k]
                if k in required:
                    required.remove(k)
                    file_required = True
        return file_required
