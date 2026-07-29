"""
JetStream Worker.

This module implements a durable pull-consumer worker.

The worker continuously fetches batches of messages from JetStream,
processes each message, and acknowledges the result.

Why this file exists
--------------------
JetStream stores messages inside Streams.

Workers consume those messages using Durable Pull Consumers.

This implementation demonstrates:

- Pull-based message consumption
- Explicit acknowledgements
- Negative acknowledgements
- Terminating invalid messages
- Long-running processing
- Structured logging
- Robust exception handling

Concepts demonstrated
---------------------
- Pull Consumer
- Durable Consumer
- Explicit ACK
- NAK
- TERM
- In Progress ACK
- Redelivery
- Delivery Metadata
"""

from __future__ import annotations

import asyncio
import json
import logging
import socket
from json import JSONDecodeError

from nats.errors import (
    ConnectionClosedError,
    ConnectionReconnectingError,
    TimeoutError,
)

from config import (
    FETCH_BATCH_SIZE,
    FETCH_TIMEOUT,
    NAK_DELAY,
    POLL_DELAY,
    PROCESSING_DELAY,
    RECONNECT_DELAY,
    RETRY_DELAY,
)

logger = logging.getLogger(__name__)

WORKER_NAME = socket.gethostname()


async def process_order(order: dict) -> None:
    """
    Simulate business logic.

    Replace this function with your real business logic.

    Args:
        order:
            Order payload.

    Raises:
        RuntimeError:
            Temporary processing failure.
    """

    logger.info(
        "Processing Order=%s Product=%s Price=%s",
        order["id"],
        order["name"],
        order["price"],
    )

    #
    # Simulate processing.
    #
    await asyncio.sleep(PROCESSING_DELAY)


async def process_message(msg) -> None:
    """
    Process a single JetStream message.

    Message lifecycle

        Receive
            ↓
        Decode
            ↓
        in_progress()
            ↓
        Business Logic
            ↓
       ACK / NAK / TERM

    Args:
        msg:
            JetStream message.
    """

    metadata = msg.metadata

    logger.info("-" * 70)
    logger.info(
        "Stream Sequence      : %s",
        metadata.sequence.stream,
    )
    logger.info(
        "Consumer Sequence    : %s",
        metadata.sequence.consumer,
    )
    logger.info(
        "Delivery Count       : %s",
        metadata.num_delivered,
    )
    logger.info(
        "Pending Messages     : %s",
        metadata.num_pending,
    )

    try:

        #
        # Decode payload.
        #
        payload = json.loads(msg.data.decode())

        #
        # Tell JetStream that processing is still running.
        #
        await msg.in_progress()

        #
        # Execute business logic.
        #
        await process_order(payload)

        #
        # Message successfully processed.
        #
        await msg.ack()

        logger.info(
            "ACK Order=%s",
            payload["id"],
        )

    #
    # Invalid JSON.
    #
    except JSONDecodeError:

        logger.error(
            "Invalid JSON payload."
        )

        #
        # Never retry.
        #
        await msg.term()

        logger.info("TERM sent.")

    #
    # Missing required field.
    #
    except KeyError as exc:

        logger.error(
            "Missing required field: %s",
            exc,
        )

        await msg.term()

        logger.info("TERM sent.")

    #
    # Temporary application failure.
    #
    except RuntimeError as exc:

        logger.warning(
            "Temporary failure: %s",
            exc,
        )

        await msg.nak(delay=RETRY_DELAY)

        logger.info(
            "NAK sent. Retry in %s second(s).",
            RETRY_DELAY,
        )

    #
    # Unexpected failure.
    #
    except Exception:

        logger.exception(
            "Unexpected processing failure."
        )

        await msg.nak(delay=NAK_DELAY)

        logger.info(
            "NAK sent."
        )


async def start_worker(psub) -> None:
    """
    Start the worker.

    This function continuously pulls messages from the configured
    durable consumer.

    Args:
        psub:
            PullSubscription.
    """

    logger.info("=" * 80)
    logger.info("Worker Started")
    logger.info("Worker Name : %s", WORKER_NAME)
    logger.info("=" * 80)

    while True:

        try:

            messages = await psub.fetch(
                batch=FETCH_BATCH_SIZE,
                timeout=FETCH_TIMEOUT,
            )

            logger.info(
                "Fetched %d message(s).",
                len(messages),
            )

            for msg in messages:
                await process_message(msg)

        except TimeoutError:

            logger.debug(
                "No messages available."
            )

            await asyncio.sleep(POLL_DELAY)

        except ConnectionReconnectingError:

            logger.warning(
                "NATS reconnecting..."
            )

            await asyncio.sleep(RECONNECT_DELAY)

        except ConnectionClosedError:

            logger.error(
                "NATS connection closed."
            )

            break

        except asyncio.CancelledError:

            logger.info(
                "Worker cancelled."
            )

            raise

        except Exception:

            logger.exception(
                "Unexpected worker failure."
            )

            await asyncio.sleep(RECONNECT_DELAY)

    logger.info("Worker stopped.")