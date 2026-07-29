"""
Subscriber example using Username/Password authentication.

This module connects to a NATS server using username/password
authentication and subscribes to messages on a subject.
"""

from __future__ import annotations

import asyncio

from nats.aio.msg import Msg

from week_6.logger import get_logger
from week_6.nats_client import NATSClient

logger = get_logger(__name__)

NATS_SERVER = "nats://localhost:4222"
SUBJECT = "hello.test"

USERNAME = "producer"
PASSWORD = "1234567890"


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
    Connect to the NATS server using username/password authentication
    and subscribe to a subject.
    """
    client = NATSClient(
        servers=[NATS_SERVER],
        user=USERNAME,
        password=PASSWORD,
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