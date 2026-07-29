"""
Publisher example using Username/Password authentication.

This module connects to a NATS server using username/password
authentication and publishes a message to a subject.
"""

from __future__ import annotations

import asyncio

from week_6.logger import get_logger
from week_6.nats_client import NATSClient

logger = get_logger(__name__)

NATS_SERVER = "nats://localhost:4222"
SUBJECT = "hello.test"

USERNAME = "producer"
PASSWORD = "1234567890"


async def main() -> None:
    """
    Connect to the NATS server using username/password authentication
    and publish a message.
    """
    client = NATSClient(
        servers=[NATS_SERVER],
        user=USERNAME,
        password=PASSWORD,
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