"""
NATS Client.

This module is responsible for establishing and managing the connection
to the NATS server.

Why this file exists
--------------------
Every component in the application (publisher, worker, stream setup,
consumer setup, etc.) requires a NATS connection.

Instead of duplicating the connection logic everywhere, it is
centralized in this module.

Concepts demonstrated
---------------------
- NATS Connection
- JetStream Context
- Connection Lifecycle Callbacks
- Automatic Reconnection
- Graceful Connection Management
"""

from __future__ import annotations

import logging

import nats
from nats.aio.client import Client
from nats.js import JetStreamContext

from config import (
    CLIENT_NAME,
    CONNECT_TIMEOUT,
    MAX_RECONNECT_ATTEMPTS,
    NATS_URL,
    RECONNECT_WAIT,
)

logger = logging.getLogger(__name__)


async def get_js() -> tuple[Client, JetStreamContext]:
    """
    Create a connection to the NATS server and return a JetStream context.

    The connection is configured with lifecycle callbacks so that
    connection state changes (disconnects, reconnects, errors, etc.)
    are visible in the application logs.

    Returns:
        tuple[Client, JetStreamContext]:
            Connected NATS client and JetStream context.

    Raises:
        nats.errors.Error:
            If the initial connection cannot be established.
    """

    nc: Client

    async def disconnected_cb() -> None:
        """Called when the client loses connection to the server."""
        logger.warning("Disconnected from NATS server.")

    async def reconnected_cb() -> None:
        """Called after successfully reconnecting."""
        logger.info(
            "Reconnected to NATS server (%s).",
            nc.connected_url.netloc,
        )

    async def error_cb(err: Exception) -> None:
        """
        Called when an asynchronous client error occurs.

        Args:
            err:
                Exception reported by the NATS client.
        """
        logger.exception("NATS asynchronous error: %s", err)

    async def closed_cb() -> None:
        """Called when the connection has been permanently closed."""
        logger.info("NATS connection closed.")

    async def discovered_server_cb() -> None:
        """
        Called when the client discovers another server in the cluster.

        Useful when connected to clustered NATS deployments.
        """
        logger.info("Discovered a new NATS server.")

    logger.info("Connecting to NATS server...")
    logger.info("Server URL : %s", NATS_URL)
    logger.info("Client Name: %s", CLIENT_NAME)

    nc = await nats.connect(
        servers=[NATS_URL],
        name=CLIENT_NAME,

        # Connection lifecycle callbacks
        disconnected_cb=disconnected_cb,
        reconnected_cb=reconnected_cb,
        error_cb=error_cb,
        closed_cb=closed_cb,
        discovered_server_cb=discovered_server_cb,

        # Reconnection behaviour
        allow_reconnect=True,
        reconnect_time_wait=RECONNECT_WAIT,
        max_reconnect_attempts=MAX_RECONNECT_ATTEMPTS,
        connect_timeout=CONNECT_TIMEOUT,
    )

    logger.info(
        "Connected successfully to %s",
        nc.connected_url.netloc,
    )

    js = nc.jetstream()

    logger.info("JetStream context initialized.")

    return nc, js