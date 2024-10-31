import json
import math
from urllib.parse import parse_qs


async def app(scope, receive, send) -> None:
    if not scope['type'] == 'http' or not scope['method'] == 'GET':
        return await send_answer(send, 404, {'error': 'Not Found'})

    path = scope['path']
    if path == '/factorial':

        qs = scope['query_string']
        qs = parse_qs(qs)
        if b'n' not in qs or len(qs[b'n']) > 1:
            return await send_answer(send, 422,
                                     {
                                         'error': 'Unprocessable Entity, must be a non-negative integer n query parameter'})

        try:
            n = int(qs[b'n'][0])
        except (IndexError, ValueError):
            return await send_answer(send, 422,
                                     {
                                         'error': 'Unprocessable Entity, must be a non-negative integer n query parameter'})

        if n < 0:
            return await send_answer(send, 400, {'error': 'Invalid value for n, must a be non-negative'})

        result = math.factorial(n)

        return await send_answer(send, 200, {'result': result})

    elif path.startswith('/fibonacci/'):

        try:
            n = int(path[len('/fibonacci/'):])
        except (IndexError, ValueError):
            return await send_answer(send, 422,
                                     {'error': 'Unprocessable Entity, must be a non-negative integer path parameter'})

        if n < 0:
            return await send_answer(send, 400, {'error': 'Invalid value for n, must be non-negative'})

        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        result = b

        return await send_answer(send, 200, {'result': result})

    elif path == '/mean':



        try:
            numbers = json.loads((await receive()).get('body'))
        except (IndexError, ValueError):
            return await send_answer(send, 422,
                                     {'error': 'Unprocessable Entity, must be non-empty array of floats in body'})
        if numbers is None:
            return await send_answer(send, 422,
                                     {'error': 'Invalid value for body, must be non-empty array of floats'})

        if len(numbers) == 0:
            return await send_answer(send, 400,
                                     {'error': 'Invalid value for body, must be non-empty array of floats'})

        if not all(isinstance(x, (float, int)) for x in numbers):
            return await send_answer(send, 422,
                                     {'error': 'Unprocessable Entity, all numbers must be a float'})

        result = sum(numbers) / len(numbers)

        return await send_answer(send, 200, {'result': result})

    else:

        return await send_answer(send, 404, {'error': 'Not Found'})


async def send_answer(send, status_code: int, body: dict) -> None:
    headers = [(b'content-type', b'application/json')]
    body_bytes = json.dumps(body).encode()

    await send({
        'type': 'http.response.start',
        'status': status_code,
        'headers': headers
    })

    await send({
        'type': 'http.response.body',
        'body': body_bytes
    })
