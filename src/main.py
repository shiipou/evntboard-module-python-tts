import asyncio
import json
import os
import uuid
import websockets
import requests
import logging
from jsonrpcserver import method, async_dispatch as dispatch
from jsonrpcclient import Ok, parse_json, request_json, request

# Constants
EVNTBOARD_HOST = os.getenv('EVNTBOARD_HOST')
MODULE_CODE = os.getenv('MODULE_CODE') or 'coqui'
MODULE_NAME = os.getenv('MODULE_NAME')
MODULE_TOKEN = os.getenv('MODULE_TOKEN')

if not EVNTBOARD_HOST:
    raise ValueError("EVNTBOARD_HOST not set")

if not MODULE_NAME:
    raise ValueError("MODULE_NAME not set")

if not MODULE_TOKEN:
    raise ValueError("MODULE_TOKEN not set")

COQUI_HOST = None

# Define JSON-RPC methods
@method
def tts(text, lang, voice):
    url = f"{COQUI_HOST}/api/tts?text={text}&speaker_id={voice}&language_id={lang}"

    response = requests.get(url)
    if response.status_code == 200:
        print(f'Test={response.text}')
        return response.text
    else:
        return f"Error: {response.status_code}"


# More methods can be defined here...

async def main():
    print(f'EVNTBOARD_HOST={EVNTBOARD_HOST}')
    async with websockets.connect(EVNTBOARD_HOST) as ws:
        # Register session
        await ws.send(request_json("session.register", params={
            'code': MODULE_CODE,
            'name': MODULE_NAME,
            'token': MODULE_TOKEN
        }))

        result = parse_json(await ws.recv())
        if isinstance(result, Ok):
            COQUI_HOST = [c['value'] for c in result.result if c['key'] == 'host'][0] or None
            async for message in ws:
                # Incoming message (request)
                request = json.loads(message)
                print(f'Request={request}')

                # Dispatch the request to the appropriate method
                response = await dispatch(request)
                print(f'Response={response}')

                if response.wanted:
                    # Send the response back through the WebSocket
                    await ws.send(str(response))
        else:
            logging.error(result.message)

asyncio.run(main())
