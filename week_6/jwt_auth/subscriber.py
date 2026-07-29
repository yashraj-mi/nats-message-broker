"""
Subscriber example using JWT authentication.

This module connects to a NATS server using a user credentials (.creds)
file and subscribes to order-related events.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from nats.aio.msg import Msg

from week_6.logger import get_logger
from week_6.nats_client import NATSClient

logger = get_logger(__name__)

NATS_SERVER = "nats://localhost:4222"
SUBJECT = "app.order.>"

CREDS_FILE = Path(__file__).parent / "creds" / "subscriber.creds"


async def message_handler(msg: Msg) -> None:
    """
    Handle incoming order messages.

    Args:
        msg:
            Incoming NATS message.
    """
    try:
        logger.info(
            "Received message on '%s': %s",
            msg.subject,
            msg.data.decode(),
        )
    except UnicodeDecodeError:
        logger.warning(
            "Received non UTF-8 message on subject '%s'.",
            msg.subject,
        )


async def main() -> None:
    """
    Connect to the NATS server using JWT authentication and subscribe
    to order events.

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

        await client.subscribe(
            subject=SUBJECT,
            callback=message_handler,
        )

        logger.info(
            "Listening for messages on '%s'. Press Ctrl+C to stop.",
            SUBJECT,
        )

        await client.wait_forever()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())