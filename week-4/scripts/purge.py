"""
Purge all messages from the stream.

The stream remains.
Only stored messages are removed.

Usage:
    python scripts/purge_stream.py
"""

from __future__ import annotations

import asyncio
import logging

from config import STREAM
from logger import configure_logger
from nats_client import get_js

logger = logging.getLogger(__name__)


async def main() -> None:
    """Purge every message from the stream."""

    configure_logger()

    nc, js = await get_js()

    try:
        logger.info("Purging stream '%s'...", STREAM)

        await js.purge_stream(STREAM)

        logger.info("Stream successfully purged.")

    finally:
        await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())