import asyncio
import json

import nats
from nats.aio.msg import Msg

# Configuration
NATS_SERVER = "nats://localhost:4222"
SUBJECT = "product.created"


async def main() -> None:
    """
    Connect to the NATS server and subscribe to product creation events.

    The subscriber listens on the `product.created` subject and prints
    the product name and price whenever a new event is received.
    """

    async def disconnected_cb() -> None:
        """Called when the client disconnects from the NATS server."""
        print("Disconnected from the NATS server.")

    async def error_cb(error: Exception) -> None:
        """Called when the client encounters an error."""
        print(f"Error: {error}")

    async def reconnect_cb() -> None:
        """Called after the client successfully reconnects."""
        print(f"Reconnected to: {nc.connected_url.netloc}")

    async def closed_cb() -> None:
        """Called when the connection is permanently closed."""
        print("Connection to the NATS server has been closed.")

    # Establish a connection to the NATS server.
    nc = await nats.connect(
        NATS_SERVER,
        error_cb=error_cb,
        disconnected_cb=disconnected_cb,
        reconnected_cb=reconnect_cb,
        closed_cb=closed_cb,
        allow_reconnect=True,
        verbose=True,
        name="NATS-server"
    )

    async def message_handler(msg: Msg) -> None:
        """
        Process incoming product creation events.

        Args:
            msg: The NATS message containing the product details in JSON format.
        """
        data = json.loads(msg.data.decode("utf-8"))

        print(
            f"Product: {data['product_name']}, "
            f"Price: ${data['product_price']}"
        )

    # Subscribe to the subject.
    await nc.subscribe(
        SUBJECT,
        cb=message_handler,
    )

    print(f"Listening for messages on '{SUBJECT}'...")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down subscriber...")
    finally:
        await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())