"""
JetStream Stream Management.

This module is responsible for creating and validating the application's
JetStream stream.

Why this file exists
--------------------
JetStream persists messages inside Streams.

Before any publisher can publish messages or any consumer can consume
them, the Stream must exist.

This module ensures that:

- The stream exists.
- Stream creation is idempotent.
- Useful stream metadata is logged.

Concepts demonstrated
---------------------
- JetStream Streams
- Idempotent resource creation
- Stream metadata
- Administrative APIs
"""

from __future__ import annotations

import logging

from nats.js.errors import NotFoundError

from config import STREAM

logger = logging.getLogger(__name__)


async def setup_stream(js) -> None:
    """
    Ensure the JetStream stream exists.

    If the stream already exists, its metadata is logged.
    Otherwise, a new stream is created.

    Args:
        js:
            JetStream context.

    Raises:
        Exception:
            Propagates unexpected JetStream errors.
    """

    logger.info("Checking stream '%s'...", STREAM)

    try:
        stream = await js.stream_info(STREAM)

        logger.info("Stream already exists.")
        logger.info("Name        : %s", stream.config.name)
        logger.info("Subjects    : %s", ", ".join(stream.config.subjects))
        logger.info("Messages    : %s", stream.state.messages)
        logger.info("Consumers   : %s", stream.state.consumers)
        logger.info("Bytes       : %s", stream.state.bytes)

    except NotFoundError:

        logger.info(
            "Stream '%s' not found. Creating a new stream...",
            STREAM,
        )

        stream = await js.add_stream(
            name=STREAM,
            subjects=["order.*"],
        )

        logger.info("Stream created successfully.")
        logger.info("Name        : %s", stream.config.name)
        logger.info("Subjects    : %s", ", ".join(stream.config.subjects))

    except Exception:

        logger.exception(
            "Failed to initialize stream '%s'.",
            STREAM,
        )

        raise