from logging_config import get_logger

logger=get_logger()

async def disconnected_cb():
    """
    Handle NATS disconnection events.

    This callback is invoked automatically when the client loses its
    connection to the NATS server.
    """
    logger.warning("Disconnected from NATS")


async def reconnected_cb():
    """
    Handle successful reconnection to the NATS server.

    This callback is triggered when the client successfully reconnects
    after a disconnection.
    """
    logger.info("Reconnected")


async def closed_cb():
    """
    Handle NATS connection closure.

    This callback is called when the NATS connection has been permanently
    closed and will no longer attempt to reconnect.
    """
    logger.info("Connection closed")


async def error_cb(e: Exception):
    """
    Handle asynchronous NATS client errors.

    Args:
        e: The exception raised by the NATS client.
    """
    logger.exception("NATS Error: %s", e)