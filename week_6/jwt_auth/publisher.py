"""
Publisher example using JWT authentication.

This module connects to a NATS server using a user credentials (.creds)
file and publishes a message to a subject.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from week_6.logger import get_logger
from week_6.nats_client import NATSClient

logger = get_logger(__name__)

NATS_SERVER = "nats://localhost:4222"
SUBJECT = "app.order.created"

CREDS_FILE = Path(__file__).parent / "creds" / "publisher.creds"


async def main() -> None:
    """
    Connect to the NATS server using JWT authentication and publish
    a message.

    Raises:
        FileNotFoundError:
            If the credentials file does not exist.
    """
    if not CREDS_FILE.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {CREDS_FILE}"
        )

    client = NATSClient(
        servers=[NATS_SERVER],
        user_credentials=str(CREDS_FILE),
    )

    try:
        await client.connect()

        message = b"Hello from Python publisher!"

        logger.info(
            "Publishing message to subject '%s'.",
            SUBJECT,
        )

        await client.publish(
            subject=SUBJECT,
            payload=message,
        )

        logger.info("Message published successfully.")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())