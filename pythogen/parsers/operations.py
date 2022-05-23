import logging
from dataclasses import dataclass
from typing import Any

from pythogen import models
from pythogen.parsers.parameters import ParameterParser
from pythogen.parsers.references import RefResolver
from pythogen.parsers.request_body import RequestBodyParser
from pythogen.parsers.response import ResponseParser
from pythogen.parsers.schemas import SchemaParser


logger = logging.getLogger(__name__)


@dataclass
class ParsedOperation:
    operation: models.OperationObject
    inline_schemas: dict[str, models.SchemaObject]


class OperationParser:
    def __init__(
        self,
        ref_resolver: RefResolver,
        schema_parser: SchemaParser,
        response_parser: ResponseParser,
        request_body_parser: RequestBodyParser,
        parameters_parser: ParameterParser,
    ) -> None:
        self._ref_resolver = ref_resolver
        self._schema_parser = schema_parser
        self._response_parser = response_parser
        self._request_body_parser = request_body_parser
        self._parameters_parser = parameters_parser

    def parse_item(self, method: models.HttpMethod, operation_data: dict[str, Any]) -> ParsedOperation:
        """Спарсить спецификацию метода ручки (POST-, GET-, PUT-запроса и т.п.)"""
        responses: dict[str, models.ResponseObject] = {}
        inline_schemas: dict[str, models.SchemaObject] = {}

        for status_code, response_data in operation_data.get('responses').items():
            if status_code == 'default':
                logger.error('Unable to parse responses, "default" not implemented yet')
                continue

            if ref := response_data.get('$ref', None):
                resolved_ref = self._ref_resolver.resolve(ref)
                response_data = resolved_ref.ref_data
                response_id = resolved_ref.ref_id
            else:
                response_id = f"{operation_data['summary'].replace(' ', '')}Response{status_code}"

            parsed_response = self._response_parser.parse_item(response_id, response_data)
            responses[status_code] = parsed_response.response
            inline_schemas.update(parsed_response.inline_schemas)

        request_body_data = operation_data.get('requestBody')
        if request_body_data:
            request_body = self._request_body_parser.parse_item(request_body_data)
        else:
            request_body = None

        parameters = []
        for parameter_data in operation_data.get('parameters', []):
            if ref := parameter_data.get('$ref', None):
                resolved_ref = self._ref_resolver.resolve(ref)
                parameter = self._parameters_parser.parse_item(resolved_ref.ref_id, resolved_ref.ref_data)
                parameters.append(parameter)
            else:
                parameter_id = f'<inline+{models.ParameterObject.__name__}>'
                parameter = self._parameters_parser.parse_item(parameter_id, parameter_data)
                parameters.append(parameter)

        return ParsedOperation(
            operation=models.OperationObject(
                method=method,
                summary=operation_data.get('summary'),
                description=operation_data.get('description'),
                operation_id=operation_data.get('operationId'),
                request_body=request_body,
                responses=models.ResponsesObject(patterned=responses),
                parameters=parameters,
            ),
            inline_schemas=inline_schemas,
        )
