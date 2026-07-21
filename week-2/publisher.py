"""
NATS publisher example.

This module connects to a NATS server and publishes sample user creation
events to the ``user.created`` subject. It also demonstrates connection
lifecycle callbacks for monitoring connection status.
"""

import asyncio
import json
import random
import nats

from logging_config import get_logger
from event_cb import  disconnected_cb,reconnected_cb,closed_cb,error_cb

logger = get_logger()

async def main():
    """
    Connect to the NATS server and publish sample user events.

    The function performs the following steps:
        1. Establishes a connection to the NATS server.
        2. Registers lifecycle callbacks for connection events.
        3. Publishes 45 JSON-encoded user messages to the
           ``user.created`` subject.
        4. Flushes pending messages to ensure delivery.
        5. Gracefully drains and closes the connection.
    """
    nc = await nats.connect(
        servers=[
            "nats://localhost:4222",
            # "nats://localhost:4223",
            # "nats://localhost:4224",
        ],
        disconnected_cb=disconnected_cb,
        reconnected_cb=reconnected_cb,
        closed_cb=closed_cb,
        error_cb=error_cb,
        max_reconnect_attempts=-1,
        reconnect_time_wait=2,
    )

    try:
        for i in range(45):
            payload = {
                "id": i + 1,
                "name": "Yashraj",
                "age": random.randint(20, 30),
            }

            await nc.publish(
                subject="user.created",
                payload=json.dumps(payload).encode(),
            )

            logger.info("Published: %s", payload)

        # Ensure all buffered messages reach the server.
        await nc.flush()

    finally:
        # Gracefully close the connection after all pending messages
        # have been sent.
        await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())