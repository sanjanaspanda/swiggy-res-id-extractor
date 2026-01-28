import asyncio
import websockets


async def test_ws():
    uri = "ws://localhost:8000/api/v1/bulk/ws/test-job-id"
    async with websockets.connect(uri) as websocket:
        print("Connected!")
        await websocket.close()


if __name__ == "__main__":
    asyncio.run(test_ws())
