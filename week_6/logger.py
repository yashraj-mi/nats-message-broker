"""
Application logging configuration.

This module exposes a reusable logger configured for the entire application.
"""

from __future__ import annotations

import logging
from logging import Logger


def get_logger(name: str = "nats-app") -> Logger:
    """
    Create and return a configured logger.

    The logger is configured only once. Subsequent calls return the same
    logger instance without adding duplicate handlers.

    Args:
        name:
            Name of the logger.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.propagate = False

    return logger