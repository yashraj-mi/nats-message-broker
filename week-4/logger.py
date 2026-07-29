"""
Application logging configuration.

This module centralizes the logging configuration for the entire
JetStream learning project.

Why this file exists
--------------------
Every module in the project should use the standard Python logging
library instead of print() statements.

Having a single logging configuration ensures:

- Consistent log formatting
- Consistent log levels
- Easier debugging
- Easy future integration with log files, ELK, Loki, Splunk, etc.

This module should be initialized exactly once during application
startup.

Concepts demonstrated
---------------------
- Centralized logging
- Structured logging
- Logger hierarchy
- Console logging
"""

from __future__ import annotations

import logging
import sys


LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)-8s | "
    "%(name)s | "
    "%(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logger(level: int = logging.INFO) -> None:
    """
    Configure the root logger.

    This function should only be called once when the application
    starts. Every module should obtain its own logger using:

        logger = logging.getLogger(__name__)

    Args:
        level:
            Logging level.
            Defaults to logging.INFO.

    Returns:
        None
    """

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stdout,
        force=True,
    )

    #
    # Reduce noisy logs from third-party libraries.
    #
    logging.getLogger("nats").setLevel(logging.INFO)

    logger = logging.getLogger(__name__)

    logger.info("=" * 70)
    logger.info("Logging initialized")
    logger.info("Log Level : %s", logging.getLevelName(level))
    logger.info("=" * 70)