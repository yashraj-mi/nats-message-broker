"""
NATS queue subscriber example.

This module connects to a NATS server and starts multiple queue subscribers
that listen for messages published on the ``user.created`` subject. Messages
are distributed among the subscribers using the ``user-workers`` queue group,
allowing work to be processed in a load-balanced manner.
"""

from __future__ import annotations

import asyncio
import json
import signal

import nats
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.errors import Error, TimeoutError

from event_cb import (
    closed_cb,
    disconnected_cb,
    error_cb,
    reconnected_cb,
)
from logging_config import get_logger

logger = get_logger()


async def listener(nc: Client, name: str) -> None:
    """
    Create and register a queue subscriber.

    Args:
        nc:
            Active NATS connection.

        name:
            Worker identifier.
    """

    async def handler(msg: Msg) -> None:
        """
        Process an incoming message.

        Args:
            msg:
                Received NATS message.
        """
        try:
            data = json.loads(msg.data.decode())

            logger.info(
                "[Worker %s] Received: %s",
                name,
                data,
            )

            # Simulate business logic.
            await asyncio.sleep(1)

            logger.info(
                "[Worker %s] Processing completed.",
                name,
            )

        except json.JSONDecodeError:
            logger.exception(
                "[Worker %s] Invalid JSON payload.",
                name,
            )

        except Exception:
            logger.exception(
                "[Worker %s] Failed to process message.",
                name,
            )

    await nc.subscribe(
        subject="user.created",
        queue="user-workers",
        cb=handler,
    )

    logger.info(
        "Worker %s subscribed.",
        name,
    )


async def main() -> None:
    """
    Start queue subscribers and wait for shutdown.
    """
    stop_event = asyncio.Event()
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
            reconnect_time_wait=2,
            max_reconnect_attempts=-1,
        )

        logger.info(
            "Connected to %s",
            nc.connected_url,
        )

        await asyncio.gather(
            listener(nc, "A"),
            listener(nc, "B"),
            listener(nc, "C"),
        )

        logger.info("All workers are ready.")

        loop = asyncio.get_running_loop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                stop_event.set,
            )

        await stop_event.wait()

        logger.info("Shutdown signal received.")

    except TimeoutError:
        logger.exception("Connection timed out.")
        raise

    except Error:
        logger.exception("A NATS error occurred.")
        raise

    except asyncio.CancelledError:
        logger.info("Subscriber cancelled.")
        raise

    except Exception:
        logger.exception("Unexpected subscriber error.")
        raise

    finally:
        if nc is not None and not nc.is_closed:
            logger.info("Draining NATS connection...")
            await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())