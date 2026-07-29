"""
Subscriber example using TLS authentication.

This module connects to a NATS server over TLS and subscribes to
messages on a subject.
"""

from __future__ import annotations

import asyncio
import ssl
from pathlib import Path

from nats.aio.msg import Msg

from week_6.logger import get_logger
from week_6.nats_client import NATSClient

logger = get_logger(__name__)

NATS_SERVER = "tls://localhost:4222"
SUBJECT = "hello.test"

TLS_DIR = Path(__file__).parent / "tls"
CA_CERT = TLS_DIR / "ca.pem"
CLIENT_CERT = TLS_DIR / "client.pem"
CLIENT_KEY = TLS_DIR / "client-key.pem"


def create_ssl_context() -> ssl.SSLContext:
    """
    Create and configure an SSL context for TLS authentication.

    Returns:
        Configured SSL context.

    Raises:
        FileNotFoundError:
            If any required TLS certificate or key file is missing.
    """
    required_files = (
        CA_CERT,
        CLIENT_CERT,
        CLIENT_KEY,
    )

    for file in required_files:
        if not file.exists():
            raise FileNotFoundError(f"TLS file not found: {file}")

    ssl_context = ssl.create_default_context(
        cafile=str(CA_CERT),
    )

    ssl_context.load_cert_chain(
        certfile=str(CLIENT_CERT),
        keyfile=str(CLIENT_KEY),
    )

    return ssl_context


async def message_handler(msg: Msg) -> None:
    """
    Process an incoming NATS message.

    Args:
        msg:
            Received NATS message.
    """
    try:
        logger.info(
            "Received message on '%s': %s",
            msg.subject,
            msg.data.decode(),
        )
    except UnicodeDecodeError:
        logger.warning(
            "Received non UTF-8 message on subject '%s'.",
            msg.subject,
        )


async def main() -> None:
    """
    Connect to the NATS server using TLS authentication and subscribe
    to a subject.
    """
    ssl_context = create_ssl_context()

    client = NATSClient(
        servers=[NATS_SERVER],
        tls=ssl_context,
    )

    try:
        await client.connect()

        await client.subscribe(
            subject=SUBJECT,
            callback=message_handler,
        )

        logger.info(
            "Listening on '%s'. Press Ctrl+C to stop.",
            SUBJECT,
        )

        await client.wait_forever()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())