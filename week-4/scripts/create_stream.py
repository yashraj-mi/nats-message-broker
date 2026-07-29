"""
Create the JetStream stream.

This script is safe to execute multiple times.

Usage:
    python scripts/create_stream.py
"""

from __future__ import annotations

import asyncio

from logger import configure_logger
from nats_client import get_js
from stream_setup import setup_stream


async def main() -> None:
    """Create the application's JetStream stream."""

    configure_logger()

    nc, js = await get_js()

    try:
        await setup_stream(js)
    finally:
        await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())