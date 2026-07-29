"""
Subscriber example using NKey authentication.

This module connects to a NATS server using an NKey seed file and
subscribes to messages on a subject.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from nats.aio.msg import Msg

from week_6.logger import get_logger
from week_6.nats_client import NATSClient

logger = get_logger(__name__)

NATS_SERVER = "nats://localhost:4222"
NKEY_SEED = Path(__file__).parent / "user.nk"
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
    Connect to the NATS server using NKey authentication and subscribe
    to a subject.

    Raises:
        FileNotFoundError:
            If the NKey seed file does not exist.
    """
    if not NKEY_SEED.exists():
        raise FileNotFoundError(
            f"NKey seed file not found: {NKEY_SEED}"
        )

    client = NATSClient(
        servers=[NATS_SERVER],
        nkeys_seed=str(NKEY_SEED),
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