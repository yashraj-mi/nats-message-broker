"""
NATS publisher example.

This module connects to a NATS server and publishes sample user creation
events to the ``user.created`` subject. It also demonstrates connection
lifecycle callbacks for monitoring connection status.
"""

from __future__ import annotations

import asyncio
import json
import random

import nats
from nats.aio.client import Client
from nats.errors import Error, TimeoutError

from logging_config import get_logger
from event_cb import (
    closed_cb,
    disconnected_cb,
    error_cb,
    reconnected_cb,
)

logger = get_logger()


async def main() -> None:
    """
    Connect to the NATS server and publish sample user events.

    Raises:
        TimeoutError:
            If the connection or publish operation times out.

        Error:
            If a NATS-specific error occurs.

        Exception:
            For any unexpected errors.
    """
    nc: Client | None = None

    try:
        logger.info("Connecting to NATS server...")

        nc = await nats.connect(
            servers=[
                "nats://localhost:4222",
                # "nats://localhost:4223",
                # "nats://localhost:4224",
            ],
            disconnected_cb=disconnected_cb,
            reconnected_cb=reconnected_cb,
            closed_cb=closed_cb,
            error_cb=error_cb,
            max_reconnect_attempts=-1,
            reconnect_time_wait=2,
        )

        logger.info("Connected to %s", nc.connected_url)

        for i in range(45):
            payload = {
                "id": i + 1,
                "name": "Yashraj",
                "age": random.randint(20, 30),
            }

            await nc.publish(
                subject="user.created",
                payload=json.dumps(payload).encode(),
            )

            logger.info("Published: %s", payload)

        await nc.flush()

        logger.info("All messages published successfully.")

    except TimeoutError:
        logger.exception("NATS operation timed out.")
        raise

    except Error:
        logger.exception("A NATS error occurred.")
        raise

    except asyncio.CancelledError:
        logger.info("Publisher task cancelled.")
        raise

    except Exception:
        logger.exception("Unexpected error while publishing messages.")
        raise

    finally:
        if nc is not None and not nc.is_closed:
            logger.info("Draining NATS connection...")
            await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())