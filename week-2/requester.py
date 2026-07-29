"""
NATS request client example.

This module connects to a NATS server and sends request messages to the
``user.is_exist`` subject using the request-reply pattern. It waits for
responses from a responder and logs the results.
"""

import asyncio
import json

import nats
from nats.errors import TimeoutError

from event_cb import (
    closed_cb,
    disconnected_cb,
    error_cb,
    reconnected_cb,
)
from logging_config import get_logger

logger = get_logger()


async def send_request(nc, payload):
    msg = await nc.request(
        subject="user.is_exist",
        payload=json.dumps(payload).encode(),
        timeout=5,
    )
    return json.loads(msg.data.decode())


async def main():
    """
    Connect to the NATS server and send request messages.

    This function performs the following steps:
        1. Establishes a connection to the NATS server.
        2. Registers connection lifecycle callbacks.
        3. Sends multiple request messages to the ``user.is_exist`` subject.
        4. Waits for a reply for each request.
        5. Logs the received responses.
        6. Gracefully drains the connection before exiting.

    Raises:
        TimeoutError:
            If no responder replies within the configured timeout.
        Exception:
            For any unexpected errors encountered during execution.
    """
    try:

        nc = await nats.connect(
            servers=["nats://localhost:4222"],
            disconnected_cb=disconnected_cb,
            reconnected_cb=reconnected_cb,
            closed_cb=closed_cb,
            error_cb=error_cb,
        )
        await nc.flush()


        payload = {
            "email": "yashraj@gmail.com",
        }

        tasks = [
            send_request(nc, payload)
            for _ in range(10)
        ]

        responses = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        for response in responses:
            if isinstance(response, Exception):
                logger.error("Request failed: %s", response)
            else:
                logger.info("Response received successfully.")
                logger.info("Response Payload: %s", response)

        for response in responses:
            logger.info("Response received successfully.")
            logger.info("Response Payload: %s", response)

    except TimeoutError:
        logger.error(
            "Request timed out. No responder available for subject 'user.is_exist'."
        )

    except Exception:
        logger.exception("Unexpected error while sending request.")

    finally:
        if nc is not None and not nc.is_closed:
            logger.info("Draining NATS connection...")
            await nc.drain()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
