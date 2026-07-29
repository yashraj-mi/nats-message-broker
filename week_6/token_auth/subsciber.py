"""
Subscriber example using token-based authentication.

This module connects to a NATS server using an authentication token
and subscribes to messages on a subject.
"""

from __future__ import annotations

import asyncio

from nats.aio.msg import Msg

from logger import get_logger
from nats_client import NATSClient

logger = get_logger(__name__)

NATS_SERVER = "nats://localhost:4222"
TOKEN = "secret-token-12345-xyz77"
SUBJECT = "hello.test"


async def message_handler(msg: Msg) -> None:
    """
    Handle an incoming NATS message.

    Args:
        msg:
            Received NATS message.
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
    Connect to the NATS server using token authentication and
    subscribe to a subject.
    """
    client = NATSClient(
        servers=[NATS_SERVER],
        token=TOKEN,
    )

    try:
        await client.connect()

        await client.subscribe(
            subject=SUBJECT,
            callback=message_handler,
        )

        logger.info(
            "Listening on '%s'. Press Ctrl+C to stop.",
            SUBJECT,
        )

        await client.wait_forever()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())