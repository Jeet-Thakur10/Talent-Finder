import asyncio

import websockets


async def test():

    uri = "ws://localhost:8000/ws"

    async with websockets.connect(uri) as websocket:

        msg = input("Enter a message: ")

        await websocket.send(f"hello , my msg {msg}")

        response = await websocket.recv()

        print(response)

asyncio.run(test())
