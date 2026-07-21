import asyncio
import json
import random

import nats

# Configuration
NATS_SERVER = "nats://localhost:4222"
SUBJECT = "product.created"
TOTAL_MESSAGES = 10


async def main() -> None:
    """
    Connect to the NATS server and publish sample product creation events.

    This script publishes `TOTAL_MESSAGES` JSON messages to the
    `product.created` subject. Each message contains a randomly
    generated product price and a fixed product name.
    """
    # Establish a connection to the NATS server.
    nc = await nats.connect(NATS_SERVER)

    try:
        for _ in range(TOTAL_MESSAGES):
            payload = {
                "product_name": "TVS Keyboard",
                "product_price": random.randint(500, 5000),
            }

            await nc.publish(
                SUBJECT,
                json.dumps(payload).encode("utf-8"),
            )

        print(f"Successfully published {TOTAL_MESSAGES} messages to '{SUBJECT}'.")

    finally:
        # Gracefully close the connection.
        await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())