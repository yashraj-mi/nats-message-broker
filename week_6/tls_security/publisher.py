"""
Publisher example using TLS authentication.

This module connects to a NATS server over TLS and publishes a
message to a subject.
"""

from __future__ import annotations

import asyncio
import ssl
from pathlib import Path

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
    Creates an SSL context. Server validation uses the Linux system store,
    while client identity is loaded from local files.
    """
    # 1. Automatically loads the  installed ca.crt from the Linux system store
    ssl_context = ssl.create_default_context()

    # 2. Keep these local as files, as Python on Linux cannot fetch 
    # client private keys out of a system-wide store natively.
    if not CLIENT_CERT.exists() or not CLIENT_KEY.exists():
        raise FileNotFoundError("Client certificate or key file is missing.")

    ssl_context.load_cert_chain(
        certfile=str(CLIENT_CERT),
        keyfile=str(CLIENT_KEY),
    )

    return ssl_context



async def main() -> None:
    """
    Connect to the NATS server using TLS authentication and publish a
    message.
    """
    ssl_context = create_ssl_context()

    client = NATSClient(
        servers=[NATS_SERVER],
        tls=ssl_context,
    )

    try:
        await client.connect()

        payload = b"Hello, Yashraj"

        logger.info(
            "Publishing message to subject '%s'.",
            SUBJECT,
        )

        await client.publish(
            subject=SUBJECT,
            payload=payload,
        )

        logger.info("Message published successfully.")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())