"""
NATS queue subscriber example.

This module connects to a NATS server and starts multiple queue subscribers
that listen for messages published on the ``user.created`` subject. Messages
are distributed among the subscribers using the ``user-workers`` queue group,
allowing work to be processed in a load-balanced manner.
"""

import asyncio
import json
import signal

import nats

from event_cb import (
    closed_cb,
    disconnected_cb,
    error_cb,
    reconnected_cb,
)
from logging_config import get_logger

logger = get_logger()


async def listener(nc: nats.NATS, name: str):
    """
    Create and register a queue subscriber.

    This function subscribes a worker to the ``user.created`` subject using
    the ``user-workers`` queue group. Each message is processed by only one
    worker in the group, enabling load balancing.

    Args:
        nc: An active NATS client connection.
        name: A unique identifier used for logging the worker's activity.
    """

    async def handler(msg):
        """
        Process an incoming NATS message.

        The message payload is decoded from JSON and represents a user
        creation event. The function simulates business logic before
        acknowledging completion through logging.

        Args:
            msg: The NATS message received by the subscriber.
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

        except json.JSONDecodeError:
            logger.exception(
                "[Worker %s] Invalid JSON",
                name,
            )

        except Exception:
            logger.exception(
                "[Worker %s] Failed to process message",
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


async def main():
    """
    Start the NATS queue subscribers and wait for shutdown.

    This function performs the following steps:
        1. Connects to the NATS server.
        2. Registers connection lifecycle callbacks.
        3. Starts three queue subscribers (workers).
        4. Waits for a termination signal (SIGINT or SIGTERM).
        5. Gracefully drains the NATS connection before exiting.
    """
    stop_event = asyncio.Event()

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

    logger.info("Shutting down...")

    await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())