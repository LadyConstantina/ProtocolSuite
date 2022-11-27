import asyncio
import websockets
import time

async def send_heartbeat():
    try:
        async with websockets.connect("ws://localhost:8765", ping_interval=None, close_timeout=1) as websocket:
            await websocket.send("heartbeat")
            confirm = await websocket.recv()
            print(confirm)
            time.sleep(15)
    except:
        raise ArithmeticError

async def echo(websocket):
    async for message in websocket:
        await websocket.send("confirm")

async def main():
    async with websockets.serve(echo, "localhost", 8765):
        await asyncio.Future()  # run forever

