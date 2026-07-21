"""
Logging configuration utilities.

This module provides a helper function to retrieve configured logger
instances for use across the application.
"""

import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def get_logger():
    """
    Create and return a logger for the calling module.

    The logger uses the module name as its identifier and inherits the
    global logging configuration defined in this module.

    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(__name__)