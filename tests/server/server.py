import asyncio
from typing import Union

from aiohttp import web


async def get_object(request: web.Request) -> web.json_response:
    return_error = request.rel_url.query.get('return_error')
    object_id = request.match_info.get('object_id')
    if return_error == 'true':
        return web.json_response(data={'code': 'unknown_error'}, status=500)
    return web.json_response(
        data={'string_data': object_id, 'integer_data': 1, 'array_data': ['1', '2', '3'], 'boolean_data': True}
    )


async def get_object_slow(request: web.Request) -> web.json_response:
    await asyncio.sleep(1)
    return_error = request.rel_url.query.get('return_error')
    object_id = request.match_info.get('object_id')
    if return_error == 'true':
        return web.json_response(data={'code': 'unknown_error'}, status=500)
    return web.json_response(
        data={'string_data': object_id, 'integer_data': 1, 'array_data': ['1', '2', '3'], 'boolean_data': True}
    )


async def post_object(request: web.Request) -> Union[web.json_response, web.Response]:
    data = await request.json()
    if not data:
        return web.Response(status=500)

    assert 'event-data' in data

    return web.json_response(data={'status': 'OK'})


async def patch_object(request: web.Request) -> Union[web.json_response, web.Response]:
    data = await request.json()
    if not data:
        return web.Response(status=500)

    return web.json_response(data={'status': 'OK'})


async def post_object_form_data(request: web.Request) -> Union[web.json_response, web.Response]:
    data = await request.post()
    if not data:
        return web.Response(status=500, body=data)

    return web.json_response(data={'status': 'OK'})


async def post_file_multipart_form_data(request: web.Request) -> Union[web.json_response, web.Response]:
    data = await request.post()

    if not data:
        return web.Response(status=500, body=data)

    assert data["text"] == "ping"

    file: web.FileField = data["file"]
    assert file.name == "file"
    assert file.filename == "hello.txt"
    assert file.file.read() == b"hello world"

    return web.json_response(data={'status': 'OK'})


async def put_object(request: web.Request) -> Union[web.json_response, web.Response]:
    data = await request.json()
    if not data:
        return web.Response(status=500)

    return web.json_response(data={'status': 'OK'})


async def put_object_slow(request: web.Request) -> Union[web.json_response, web.Response]:
    await asyncio.sleep(1)
    data = await request.json()
    if not data:
        return web.Response(status=500)

    return web.json_response(data={'status': 'OK'})


async def delete_object(request: web.Request) -> web.json_response:
    return web.json_response(data={'status': 'OK'})


async def get_list_objects(request: web.Request) -> web.json_response:
    return web.json_response(
        data=[
            {'string_data': '1', 'integer_data': 1, 'array_data': ['1', '2', '3'], 'boolean_data': True},
            {'string_data': '1', 'integer_data': 1, 'array_data': ['1', '2', '3'], 'boolean_data': True},
        ]
    )


async def get_text(request: web.Request) -> web.Response:
    return web.Response(text='Hello')


async def get_text_as_integer(request: web.Request) -> web.Response:
    return web.Response(text='1')


async def get_allof(request: web.Request) -> web.json_response:
    return web.json_response(
        data={
            'all_of': {
                'id': '1',
                'data': 1,
            }
        }
    )


async def get_empty(request: web.Request) -> web.Response:
    return web.Response(status=200)


async def get_binary(request: web.Request) -> web.Response:
    return web.Response(body=b'some_body')


async def get_list_of_anyof(request: web.Request) -> web.Response:
    return web.json_response(data={'anyOfChildArray': [{"name": "DogName"}, {"name": "CatName"}]})


app = web.Application()
app.add_routes(
    [
        web.get('/objects', get_list_objects),
        web.post('/objects', post_object),
        web.post('/objects-form-data', post_object_form_data),
        web.get('/objects/{object_id}', get_object),
        web.put('/objects/{object_id}', put_object),
        web.patch('/objects/{object_id}', patch_object),
        web.delete('/objects/{object_id}', delete_object),
        web.get('/text', get_text),
        web.get('/text_as_integer', get_text_as_integer),
        web.get('/allof', get_allof),
        web.get('/empty', get_empty),
        web.get('/binary', get_binary),
        web.post('/multipart-form-data', post_file_multipart_form_data),
        web.get('/slow/objects/{object_id}', get_object_slow),
        web.put('/slow/objects/{object_id}', put_object_slow),
        web.get('/nested-any-of', get_list_of_anyof),
    ]
)


if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8080)
