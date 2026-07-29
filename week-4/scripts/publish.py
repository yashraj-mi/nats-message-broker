"""
Publish demo order events.

Usage:
    python scripts/publish_orders.py
"""

from __future__ import annotations

import asyncio

from logger import configure_logger
from nats_client import get_js
from publisher import publish_orders


async def main() -> None:
    """Publish sample order events."""

    configure_logger()

    nc, js = await get_js()

    try:
        await publish_orders(js)
    finally:
        await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())