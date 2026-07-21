"""
NATS request-reply responder example.

This module starts multiple queue-based responders that listen on the
``user.is_exist`` subject. Each incoming request is processed by a single
worker in the ``user-workers`` queue group, which simulates checking whether
a user exists and returns a JSON response.
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
    Create and register a request-reply responder.

    The responder subscribes to the ``user.is_exist`` subject as part of
    the ``user-workers`` queue group. Incoming requests are distributed
    across workers, ensuring each request is handled by only one worker.

    Args:
        nc: An active NATS client connection.
        name: A unique identifier used for logging the worker's activity.
    """

    async def handler(msg):
        """
        Process an incoming request and send a response.

        The request payload is expected to contain an ``email`` field.
        A JSON response indicating whether the user exists is sent back
        to the requester's reply subject.

        Args:
            msg: The NATS request message.
        """
        try:
            request = json.loads(msg.data.decode())
            email = request["email"]

            logger.info(
                "Received request | subject=%s | email=%s",
                msg.subject,
                email,
            )

            # Simulate business logic.
            await asyncio.sleep(1)

            response = {
                "email": email,
                "is_exist": True,
            }

            await msg.respond(json.dumps(response).encode())



            logger.info(
                "Response sent | [Worker %s] | reply=%s | email=%s",
                name,
                msg.reply,
                email,
            )

        except KeyError:
            logger.error("Missing 'email' field in request.")

        except json.JSONDecodeError:
            logger.error("Invalid JSON payload.")

        except Exception:
            logger.exception("Failed to process request.")

    await nc.subscribe(
        subject="user.is_exist",
        queue="user-workers",
        cb=handler,
    )
    await nc.flush()

    logger.info("Worker %s subscribed.", name)

async def main():
    """
    Start the NATS request responders and wait for shutdown.

    This function performs the following steps:
        1. Connects to the NATS server.
        2. Registers connection lifecycle callbacks.
        3. Starts three request-reply worker responders.
        4. Waits for a termination signal (SIGINT or SIGTERM).
        5. Gracefully drains the NATS connection before exiting.
    """
    stop_event = asyncio.Event()

    nc = await nats.connect(
        servers=["nats://localhost:4222"],
        disconnected_cb=disconnected_cb,
        reconnected_cb=reconnected_cb,
        closed_cb=closed_cb,
        error_cb=error_cb,
    )

    await asyncio.gather(
        listener(nc, "A"),
        listener(nc, "B"),
        listener(nc, "C"),
    )

    logger.info("All workers are ready.")

    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    await stop_event.wait()

    logger.info("Shutting down...")

    await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())