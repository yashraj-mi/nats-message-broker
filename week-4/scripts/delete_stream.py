"""
Delete the JetStream stream.

This removes:

- Stream
- Messages
- Consumer state

Usage:
    python scripts/delete_stream.py
"""

from __future__ import annotations

import asyncio
import logging

from config import STREAM
from logger import configure_logger
from nats_client import get_js

logger = logging.getLogger(__name__)


async def main() -> None:
    """Delete the configured stream."""

    configure_logger()

    nc, js = await get_js()

    try:
        logger.warning("Deleting stream '%s'...", STREAM)

        deleted = await js.delete_stream(STREAM)

        if deleted:
            logger.info("Stream deleted successfully.")
        else:
            logger.warning("Stream was not deleted.")

    finally:
        await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())