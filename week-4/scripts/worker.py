"""
Run a JetStream worker.

Usage:
    python scripts/run_worker.py
"""

from __future__ import annotations

import asyncio

from consumer_setup import setup_consumer
from logger import configure_logger
from nats_client import get_js
from worker import start_worker


async def main() -> None:
    """Start the durable pull consumer."""

    configure_logger()

    nc, js = await get_js()

    try:
        psub = await setup_consumer(js)

        await start_worker(psub)

    finally:
        await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())