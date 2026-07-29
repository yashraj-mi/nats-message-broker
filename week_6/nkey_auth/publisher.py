"""
Publisher example using NKey authentication.

This module connects to a NATS server using an NKey seed file and
publishes a message to a subject.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from week_6.logger import get_logger
from week_6.nats_client import NATSClient

logger = get_logger(__name__)

NATS_SERVER = "nats://localhost:4222"
NKEY_SEED = Path(__file__).parent / "user.nk"
SUBJECT = "hello.test"


async def main() -> None:
    """
    Connect to the NATS server using NKey authentication and publish a
    message.

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