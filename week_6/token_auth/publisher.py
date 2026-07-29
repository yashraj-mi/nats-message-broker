"""
Publisher example using token-based authentication.

This module connects to a NATS server using a token and publishes
a message to a subject.
"""

from __future__ import annotations

import asyncio

from week_6.logger import get_logger
from week_6.nats_client import NATSClient

logger = get_logger(__name__)

NATS_SERVER = "nats://localhost:4222"
TOKEN = "secret-token-12345-xyz77"
SUBJECT = "hello.test"


async def main() -> None:
    """
    Connect to the NATS server using token authentication and publish
    a message.
    """
    client = NATSClient(
        servers=[NATS_SERVER],
        token=TOKEN,
    )

    try:
        await client.connect()

        payload = b"Hello, Yashraj"

        logger.info(
            "Publishing message to subject '%s'.",
            SUBJECT,
        )

        await client.publish(
            subject=SUBJECT,
            payload=payload,
        )

        logger.info("Message published successfully.")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())