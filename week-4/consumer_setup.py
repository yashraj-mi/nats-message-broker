"""
JetStream Consumer Management.

This module is responsible for creating or binding to the application's
durable pull consumer.

Why this file exists
--------------------
A JetStream Consumer represents a stateful view of a Stream.

Unlike a Stream, which stores messages, a Consumer tracks:

- Delivery progress
- Acknowledgements
- Redeliveries
- Consumer state

For this learning project we use a Durable Pull Consumer because it is
the recommended pattern for scalable worker applications.

Concepts demonstrated
---------------------
- Durable Consumer
- Pull Consumer
- Explicit ACK
- Consumer binding
- Consumer state
"""

from __future__ import annotations

import logging

from config import (
    DURABLE,
    STREAM,
    SUBJECT,
)

logger = logging.getLogger(__name__)


async def setup_consumer(js):
    """
    Create or bind to the application's durable pull consumer.

    If the durable consumer already exists, this function binds to it.
    Otherwise, the NATS server creates it automatically using the
    provided durable name.

    Args:
        js:
            JetStream context.

    Returns:
        PullSubscription:
            Configured pull subscription.

    Raises:
        Exception:
            Propagates unexpected JetStream errors.
    """

    logger.info("=" * 70)
    logger.info("Initializing durable pull consumer...")
    logger.info("Stream   : %s", STREAM)
    logger.info("Subject  : %s", SUBJECT)
    logger.info("Durable  : %s", DURABLE)

    try:

        psub = await js.pull_subscribe(
            subject=SUBJECT,
            stream=STREAM,
            durable=DURABLE,
        )

        logger.info("Successfully bound to durable consumer.")

        #
        # Retrieve consumer information from the server.
        #
        consumer = await js.consumer_info(
            STREAM,
            DURABLE,
        )

        logger.info("-" * 70)
        logger.info("Consumer Information")
        logger.info("-" * 70)

        logger.info("Name              : %s", consumer.name)
        logger.info("Created           : %s", consumer.created)

        logger.info("Ack Policy        : %s", consumer.config.ack_policy)
        logger.info("Ack Wait          : %s", consumer.config.ack_wait)

        logger.info("Deliver Policy    : %s", consumer.config.deliver_policy)
        logger.info("Replay Policy     : %s", consumer.config.replay_policy)

        logger.info("Pending Messages  : %d", consumer.num_pending)
        logger.info("Waiting Pulls     : %d", consumer.num_waiting)
        logger.info("Redelivered       : %d", consumer.num_redelivered)
        logger.info("Ack Pending       : %d", consumer.num_ack_pending)

        logger.info("=" * 70)

        return psub

    except Exception:

        logger.exception(
            "Failed to initialize durable consumer '%s'.",
            DURABLE,
        )

        raise