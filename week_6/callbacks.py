"""
NATS connection lifecycle callbacks.

These callbacks are passed to ``nats.connect()`` to monitor connection events.
"""

from __future__ import annotations

from nats.aio.client import Client

from week_6.logger import get_logger

logger = get_logger(__name__)


async def error_callback(error: Exception) -> None:
    """
    Called when the NATS client encounters an asynchronous error.

    Args:
        error:
            Exception raised by the client.
    """
    logger.error("NATS error: %s", error)


async def disconnected_callback() -> None:
    """
    Called when the client disconnects from the NATS server.
    """
    logger.warning("Disconnected from NATS server.")


async def reconnected_callback() -> None:
    """
    Called when the client reconnects to the NATS server.
    """
    logger.info("Successfully reconnected to NATS server.")


async def closed_callback() -> None:
    """
    Called when the NATS connection has been permanently closed.
    """
    logger.info("NATS connection closed.")


async def discovered_server_callback(server: str) -> None:
    """
    Called when the client discovers a new server in the cluster.

    Args:
        server:
            Newly discovered server address.
    """
    logger.info("Discovered server: %s", server)


async def lame_duck_mode_callback() -> None:
    """
    Called when the connected server enters Lame Duck Mode.

    Lame Duck Mode indicates that the server is preparing to shut down and
    clients should reconnect to another server.
    """
    logger.warning("Server entered Lame Duck Mode.")


async def reconnected_server_callback(nc: Client) -> None:
    """
    Log information about the server after a successful reconnect.

    Args:
        nc:
            Active NATS client instance.
    """
    logger.info("Connected to %s", nc.connected_url)