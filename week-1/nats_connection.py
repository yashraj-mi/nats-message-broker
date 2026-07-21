import asyncio
import nats


SERVER_LIST=[
            "nats://localhost:4222",
            "nats://localhost:4223",
            "nats://localhost:4224",
]

async def main()->None:

    async def disconnected_cb():
        print("Disconnected")

    async def reconnected_cb():
        print("Reconnected to:", nc.connected_url.netloc)

    async def closed_cb():
        print("Connection closed")

    async def error_cb(e):
        print(f"Error: {e}")

    nc = await nats.connect(
        servers=SERVER_LIST,
        disconnected_cb=disconnected_cb,
        reconnected_cb=reconnected_cb,
        closed_cb=closed_cb,
        error_cb=error_cb,
        reconnect_time_wait=2,
        max_reconnect_attempts=4,
    )

    print("Connected to:", nc.connected_url.netloc)

    while True:
        await asyncio.sleep(5)
        print("Current server:", nc.connected_url.netloc)


asyncio.run(main())