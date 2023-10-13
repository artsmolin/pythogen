import io
import logging
import os

import pytest

from clients import async_client
from clients import sync_client


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TEST')

TEST_SERVER_URL = "http://localhost:8080"


def _get_httpx_sync_client():
    return sync_client.Client(TEST_SERVER_URL)


def _get_httpx_async_client():
    return async_client.Client(TEST_SERVER_URL)


def test_httpx_sync_client():
    httpx_sync_client = _get_httpx_sync_client()
    response = httpx_sync_client.get_object(
        path_params=sync_client.GetObjectPathParams(object_id='123'),
        query_params=sync_client.GetObjectQueryParams(
            return_error='',
            from_='',
        )
    )
    assert isinstance(response, sync_client.GetObjectResp)

    response = httpx_sync_client.get_object(
        path_params=sync_client.GetObjectPathParams(object_id='123'),
        query_params=sync_client.GetObjectQueryParams(
            return_error='true',
            from_='',
        ),
    )
    assert isinstance(response, sync_client.UnknownError)

    data = sync_client.PostObjectData(
        string_data='string_data',
        integer_data=1,
        boolean_data=True,
        array_data=['1', '2', '3'],
        event_data={'event': 'delivered'},
        int_enum=sync_client.IntegerEnum._1,
        str_enum=sync_client.StringEnum.FIRST_FIELD,
    )
    response = httpx_sync_client.post_object(body=data)
    assert isinstance(response, sync_client.PostObjectResp)

    response = httpx_sync_client.post_form_object(body=data)
    assert isinstance(response, sync_client.PostObjectResp)

    # /objects patch
    response = httpx_sync_client.patch_object(
        body=sync_client.PatchObjectData(id='id', data=1), 
        path_params=sync_client.PatchObjectPathParams(object_id='id'),
    )
    assert isinstance(response, sync_client.PatchObjectResp)

    response = httpx_sync_client.put_object(
        body=sync_client.PutObjectData(id='id', data=1), 
        path_params=sync_client.PutObjectPathParams(object_id='id'),
    )
    assert isinstance(response, sync_client.PutObjectResp)

    response = httpx_sync_client.delete_object(
        path_params=sync_client.DeleteObjectPathParams(object_id='id'),
    )
    assert isinstance(response, sync_client.DeleteObjectResp)

    response = httpx_sync_client.get_list_objects()
    assert isinstance(response, list)
    assert isinstance(response[0], sync_client.GetObjectResp)

    response = httpx_sync_client.get_allof()
    assert isinstance(response, sync_client.AllOfResp)

    response = httpx_sync_client.get_empty()
    assert isinstance(response, sync_client.EmptyBody)

    response = httpx_sync_client.get_text()
    assert isinstance(response, str)

    response = httpx_sync_client.get_binary()
    assert isinstance(response, bytes)

    response = httpx_sync_client.get_text_as_integer()
    assert isinstance(response, int)

    response = httpx_sync_client.post_multipart_form_data(
        body=sync_client.PostFile(text="ping"),
        files=[
            (
                "file",
                ("hello.txt", io.BytesIO(b"hello world"), 'text/plain'),
            ),
        ],
    )
    assert isinstance(response, sync_client.PostObjectResp)

    httpx_sync_client.close()


@pytest.mark.asyncio
async def test_httpx_async_client():
    httpx_async_client = _get_httpx_async_client()
    response = await httpx_async_client.get_object(
        path_params=async_client.GetObjectPathParams(object_id='123'),
        query_params=async_client.GetObjectQueryParams(
            return_error='',
            from_='',
        ),
    )
    assert isinstance(response, async_client.GetObjectResp)

    response = await httpx_async_client.get_object(
        path_params=async_client.GetObjectPathParams(object_id='123'),
        query_params=async_client.GetObjectQueryParams(
            return_error='true',
            from_='',
        ),
    )
    assert isinstance(response, async_client.UnknownError)

    data = async_client.PostObjectData(
        string_data='string_data',
        integer_data=1,
        boolean_data=True,
        array_data=['1', '2', '3'],
        event_data={'event': 'delivered'},
        int_enum=async_client.IntegerEnum._1,
        str_enum=async_client.StringEnum.FIRST_FIELD,
    )
    response = await httpx_async_client.post_object(body=data)
    assert isinstance(response, async_client.PostObjectResp)

    # /objects patch
    response = await httpx_async_client.patch_object(
        body=async_client.PatchObjectData(id='id', data=1), 
        path_params=async_client.PatchObjectPathParams(object_id='id'),
    )
    assert isinstance(response, async_client.PatchObjectResp)

    response = await httpx_async_client.put_object(
        body=async_client.PutObjectData(id='id', data=1), 
        path_params=async_client.PutObjectPathParams(object_id='id'),
    )
    assert isinstance(response, async_client.PutObjectResp)

    response = await httpx_async_client.delete_object(
        path_params=async_client.DeleteObjectPathParams(object_id='id'),
    )
    assert isinstance(response, async_client.DeleteObjectResp)

    response = await httpx_async_client.get_list_objects()
    assert isinstance(response, list)
    assert isinstance(response[0], async_client.GetObjectResp)

    meta = async_client.PythogenMetaBox()
    response = await httpx_async_client.get_allof(meta=meta)
    assert isinstance(response, async_client.AllOfResp)
    assert meta.response
    assert meta.response.status_code == 200

    response = await httpx_async_client.get_empty()
    assert isinstance(response, async_client.EmptyBody)

    response = await httpx_async_client.get_text()
    assert isinstance(response, str)

    response = await httpx_async_client.get_binary()
    assert isinstance(response, bytes)

    response = await httpx_async_client.get_text_as_integer()
    assert isinstance(response, int)

    response = await httpx_async_client.post_multipart_form_data(
        body=async_client.PostFile(text="ping"),
        files=[("file", ("hello.txt", io.BytesIO(b"hello world"), 'text/plain'))],
    )
    assert isinstance(response, async_client.PostObjectResp)

    response = await httpx_async_client.response_body_list_of_anyof()
    assert isinstance(response, async_client.ListAnyOfResp)
    assert len(response.anyOfChildArray) == 2
    assert isinstance(response.anyOfChildArray[0], async_client.Dog)

    response = await httpx_async_client.get_discriminated_oneof()
    assert isinstance(response, async_client.DiscriminatedOneOfResp)
    assert isinstance(response.required_discriminated_animal, async_client.DogWithKind)
    assert response.discriminated_animal is None

    response = await httpx_async_client.getMessage(
        headers=async_client.GetMessageHeaders(x_auth_token="qwerty12345!"),
    )
    assert isinstance(response, async_client.GetMessageResp)

    await httpx_async_client.close()
