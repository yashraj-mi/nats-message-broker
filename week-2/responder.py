"""
NATS request-reply responder example.

This module starts multiple queue-based responders that listen on the
``user.is_exist`` subject. Each incoming request is processed by a single
worker in the ``user-workers`` queue group, which simulates checking whether
a user exists and returns a JSON response.
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
    Register a request-reply responder.

    Args:
        nc:
            Active NATS connection.

        name:
            Worker identifier.
    """

    async def handler(msg: Msg) -> None:
        """
        Process an incoming request and send a response.

        Args:
            msg:
                Incoming NATS request.
        """
        try:
            request = json.loads(msg.data.decode())
            email = request["email"]

            logger.info(
                "[Worker %s] Received request | subject=%s | email=%s",
                name,
                msg.subject,
                email,
            )

            # Simulate business logic.
            await asyncio.sleep(1)

            response = {
                "email": email,
                "is_exist": True,
            }

            await msg.respond(
                json.dumps(response).encode()
            )

            logger.info(
                "[Worker %s] Response sent | reply=%s | email=%s",
                name,
                msg.reply,
                email,
            )

        except KeyError:
            logger.error(
                "[Worker %s] Missing 'email' field in request.",
                name,
            )

        except json.JSONDecodeError:
            logger.error(
                "[Worker %s] Invalid JSON payload.",
                name,
            )

        except Exception:
            logger.exception(
                "[Worker %s] Failed to process request.",
                name,
            )

    await nc.subscribe(
        subject="user.is_exist",
        queue="user-workers",
        cb=handler,
    )

    await nc.flush()

    logger.info(
        "Worker %s subscribed.",
        name,
    )


async def main() -> None:
    """
    Start request-reply responders and wait for shutdown.
    """
    stop_event = asyncio.Event()
    nc: Client | None = None

    try:
        logger.info("Connecting to NATS server...")

        nc = await nats.connect(
            servers=["nats://localhost:4222"],
            disconnected_cb=disconnected_cb,
            reconnected_cb=reconnected_cb,
            closed_cb=closed_cb,
            error_cb=error_cb,
        )

        logger.info(
            "Connected to %s",
            nc.connected_url,
        )

        await asyncio.gather(
            listener(nc, "worker-1"),
            listener(nc, "worker-2"),
            listener(nc, "worker-3"),
        )

        logger.info("All workers are ready.")

        loop = asyncio.get_running_loop()

        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(
                    sig,
                    stop_event.set,
                )
        except NotImplementedError:
            logger.warning(
                "Signal handlers are not supported on this platform."
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
        logger.info("Responder cancelled.")
        raise

    except Exception:
        logger.exception("Unexpected responder error.")
        raise

    finally:
        if nc is not None and not nc.is_closed:
            logger.info("Draining NATS connection...")
            await nc.drain()