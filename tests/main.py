import asyncio
import io
import logging
import os

from clients import async_client
from clients import sync_client
from jaeger_client import Config
from opentracing.scope_managers.contextvars import ContextVarsScopeManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TEST')

TEST_SERVER_URL: str = os.getenv('TEST_SERVER_URL', 'http://host.docker.internal:8080')

config = Config(
    config={
        'sampler': {'type': 'const', 'param': 1},
        'logging': False,
        'local_agent': {'reporting_host': 'localhost', 'reporting_port': 80},
        'propagation': 'propagation',
        'enabled': False,
    },
    validate=True,
    scope_manager=ContextVarsScopeManager(),
    service_name='Test App',
)
tracer = config.initialize_tracer()


def _get_httpx_sync_client():
    return sync_client.Client(TEST_SERVER_URL)


def _get_httpx_sync_tracing_client():
    return sync_client.Client(
        TEST_SERVER_URL,
        tracer_integration=sync_client.DefaultTracerIntegration(tracer=tracer),
    )


def _get_httpx_async_client():
    return async_client.Client(TEST_SERVER_URL)


def _get_httpx_async_tracing_client():
    return async_client.Client(
        TEST_SERVER_URL,
        tracer_integration=async_client.DefaultTracerIntegration(tracer=tracer),
    )


def test_httpx_sync_client():
    httpx_sync_client = _get_httpx_sync_client()
    response = httpx_sync_client.get_object(object_id='123', return_error='', from_='')
    assert isinstance(response, sync_client.GetObjectResp)

    response = httpx_sync_client.get_object(object_id='123', return_error='true', from_='')
    assert isinstance(response, sync_client.UnknownError)

    data = sync_client.PostObjectData(
        string_data='string_data',
        integer_data=1,
        boolean_data=True,
        array_data=['1', '2', '3'],
        event_data={'event': 'delivered'},
    )
    response = httpx_sync_client.post_object(data)
    assert isinstance(response, sync_client.PostObjectResp)

    response = httpx_sync_client.post_form_object(data)
    assert isinstance(response, sync_client.PostObjectResp)

    # /objects patch
    response = httpx_sync_client.patch_object(body=sync_client.PatchObjectData(id='id', data=1), object_id='id')
    assert isinstance(response, sync_client.PatchObjectResp)

    response = httpx_sync_client.put_object(body=sync_client.PutObjectData(id='id', data=1), object_id='id')
    assert isinstance(response, sync_client.PutObjectResp)

    response = httpx_sync_client.delete_object(object_id='id')
    assert isinstance(response, sync_client.DeleteObjectResp)

    response = httpx_sync_client.get_list_objects()
    assert isinstance(response, list)
    assert isinstance(response[0], sync_client.GetObjectResp)

    response = httpx_sync_client.get_allof()
    assert isinstance(response, sync_client.AllOfResp)

    response = httpx_sync_client.get_empty()
    assert isinstance(response, sync_client.EmptyBody)

    response = httpx_sync_client.get_text()
    assert isinstance(response, sync_client.GetTextResponse200)

    response = httpx_sync_client.get_binary()
    assert isinstance(response, sync_client.GetBinaryResponse200)

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


def test_httpx_sync_tracing_client():
    httpx_sync_client = _get_httpx_sync_tracing_client()
    response = httpx_sync_client.get_object(object_id='123', return_error='', from_='')
    assert isinstance(response, sync_client.GetObjectResp)

    response = httpx_sync_client.get_object(object_id='123', return_error='true', from_='')
    assert isinstance(response, sync_client.UnknownError)

    data = sync_client.PostObjectData(
        string_data='string_data',
        integer_data=1,
        boolean_data=True,
        array_data=['1', '2', '3'],
        event_data={'event': 'delivered'},
    )
    response = httpx_sync_client.post_object(data)
    assert isinstance(response, sync_client.PostObjectResp)

    response = httpx_sync_client.post_form_object(data)
    assert isinstance(response, sync_client.PostObjectResp)

    # /objects patch
    response = httpx_sync_client.patch_object(body=sync_client.PatchObjectData(id='id', data=1), object_id='id')
    assert isinstance(response, sync_client.PatchObjectResp)

    response = httpx_sync_client.put_object(body=sync_client.PutObjectData(id='id', data=1), object_id='id')
    assert isinstance(response, sync_client.PutObjectResp)

    response = httpx_sync_client.delete_object(object_id='id')
    assert isinstance(response, sync_client.DeleteObjectResp)

    response = httpx_sync_client.get_list_objects()
    assert isinstance(response, list)
    assert isinstance(response[0], sync_client.GetObjectResp)

    response = httpx_sync_client.get_allof()
    assert isinstance(response, sync_client.AllOfResp)

    response = httpx_sync_client.get_empty()
    assert isinstance(response, sync_client.EmptyBody)

    response = httpx_sync_client.get_text()
    assert isinstance(response, sync_client.GetTextResponse200)

    response = httpx_sync_client.get_binary()
    assert isinstance(response, sync_client.GetBinaryResponse200)

    response = httpx_sync_client.post_multipart_form_data(
        body=sync_client.PostFile(text="ping"),
        files=[("file", ("hello.txt", io.BytesIO(b"hello world"), 'text/plain'))],
    )
    assert isinstance(response, sync_client.PostObjectResp)

    httpx_sync_client.close()


async def test_httpx_async_client():
    httpx_async_client = _get_httpx_async_client()
    response = await httpx_async_client.get_object(object_id='123', return_error='', from_='')
    assert isinstance(response, async_client.GetObjectResp)

    response = await httpx_async_client.get_object(object_id='123', return_error='true', from_='')
    assert isinstance(response, async_client.UnknownError)

    data = async_client.PostObjectData(
        string_data='string_data',
        integer_data=1,
        boolean_data=True,
        array_data=['1', '2', '3'],
        event_data={'event': 'delivered'},
    )
    response = await httpx_async_client.post_object(data)
    assert isinstance(response, async_client.PostObjectResp)

    response = await httpx_async_client.post_form_object(data)
    assert isinstance(response, async_client.PostObjectResp)

    # /objects patch
    response = await httpx_async_client.patch_object(body=async_client.PatchObjectData(id='id', data=1), object_id='id')
    assert isinstance(response, async_client.PatchObjectResp)

    response = await httpx_async_client.put_object(body=async_client.PutObjectData(id='id', data=1), object_id='id')
    assert isinstance(response, async_client.PutObjectResp)

    response = await httpx_async_client.delete_object(object_id='id')
    assert isinstance(response, async_client.DeleteObjectResp)

    response = await httpx_async_client.get_list_objects()
    assert isinstance(response, list)
    assert isinstance(response[0], async_client.GetObjectResp)

    response = await httpx_async_client.get_allof()
    assert isinstance(response, async_client.AllOfResp)

    response = await httpx_async_client.get_empty()
    assert isinstance(response, async_client.EmptyBody)

    response = await httpx_async_client.get_text()
    assert isinstance(response, async_client.GetTextResponse200)

    response = await httpx_async_client.get_binary()
    assert isinstance(response, async_client.GetBinaryResponse200)

    response = await httpx_async_client.post_multipart_form_data(
        body=async_client.PostFile(text="ping"),
        files=[("file", ("hello.txt", io.BytesIO(b"hello world"), 'text/plain'))],
    )
    assert isinstance(response, async_client.PostObjectResp)

    await httpx_async_client.close()


async def test_httpx_async_tracing_client():
    httpx_async_client = _get_httpx_async_tracing_client()
    response = await httpx_async_client.get_object(object_id='123', return_error='', from_='')
    assert isinstance(response, async_client.GetObjectResp)

    response = await httpx_async_client.get_object(object_id='123', return_error='true', from_='')
    assert isinstance(response, async_client.UnknownError)

    data = async_client.PostObjectData(
        string_data='string_data',
        integer_data=1,
        boolean_data=True,
        array_data=['1', '2', '3'],
        event_data={'event': 'delivered'},
    )
    response = await httpx_async_client.post_object(data)
    assert isinstance(response, async_client.PostObjectResp)

    response = await httpx_async_client.post_form_object(data)
    assert isinstance(response, async_client.PostObjectResp)

    # /objects patch
    response = await httpx_async_client.patch_object(body=async_client.PatchObjectData(id='id', data=1), object_id='id')
    assert isinstance(response, async_client.PatchObjectResp)

    response = await httpx_async_client.put_object(body=async_client.PutObjectData(id='id', data=1), object_id='id')
    assert isinstance(response, async_client.PutObjectResp)

    response = await httpx_async_client.delete_object(object_id='id')
    assert isinstance(response, async_client.DeleteObjectResp)

    response = await httpx_async_client.get_list_objects()
    assert isinstance(response, list)
    assert isinstance(response[0], async_client.GetObjectResp)

    response = await httpx_async_client.get_allof()
    assert isinstance(response, async_client.AllOfResp)

    response = await httpx_async_client.get_empty()
    assert isinstance(response, async_client.EmptyBody)

    response = await httpx_async_client.get_text()
    assert isinstance(response, async_client.GetTextResponse200)

    response = await httpx_async_client.get_binary()
    assert isinstance(response, async_client.GetBinaryResponse200)

    response = await httpx_async_client.post_multipart_form_data(
        body=async_client.PostFile(text="ping"),
        files=[("file", ("hello.txt", io.BytesIO(b"hello world"), 'text/plain'))],
    )
    assert isinstance(response, async_client.PostObjectResp)

    await httpx_async_client.close()


if __name__ == '__main__':
    test_httpx_sync_client()
    test_httpx_sync_tracing_client()
    asyncio.run(test_httpx_async_client())
    asyncio.run(test_httpx_async_tracing_client())
