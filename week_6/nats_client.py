"""
Reusable NATS client.

This module centralizes NATS connection management including:

- Connection creation
- Graceful shutdown
- Publishing
- Subscribing
- Request/Reply

All authentication methods are supported by passing the appropriate
arguments to the constructor.

Examples:
    Username/Password:
        client = NATSClient(
            servers=["nats://localhost:4222"],
            user="producer",
            password="1234567890",
        )

    Token:
        client = NATSClient(
            servers=["nats://localhost:4222"],
            token="secret-token",
        )

    NKey:
        client = NATSClient(
            servers=["nats://localhost:4222"],
            nkeys_seed="user.nk",
        )

    TLS:
        client = NATSClient(
            servers=["tls://localhost:4222"],
            tls=ssl_context,
        )

    JWT:
        client = NATSClient(
            servers=["nats://localhost:4222"],
            user_credentials="publisher.creds",
        )
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

import nats
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.errors import Error, TimeoutError
import asyncio
from week_6.callbacks import (
    closed_callback,
    disconnected_callback,
    error_callback,
    reconnected_callback,
)
from week_6.logger import get_logger

logger = get_logger(__name__)


class NATSClient:
    """
    Reusable NATS client.

    This class wraps the nats-py client and provides a single
    interface for all authentication mechanisms.
    """

    def __init__(self, **connection_options: Any) -> None:
        """
        Initialize the client.

        Args:
            **connection_options:
                Any arguments accepted by ``nats.connect()``.
        """
        self._connection_options = connection_options
        self._nc: Client | None = None

    @property
    def connection(self) -> Client:
        """
        Return the active NATS connection.

        Raises:
            RuntimeError:
                If the client is not connected.
        """
        if self._nc is None:
            raise RuntimeError("NATS client is not connected.")

        return self._nc

    async def connect(self) -> Client:
        """
        Establish a connection to the NATS server.

        Returns:
            Connected NATS client.

        Raises:
            TimeoutError:
                If connection times out.

            Error:
                If a NATS error occurs.
        """
        try:
            logger.info("Connecting to NATS server...")

            self._nc = await nats.connect(
                error_cb=error_callback,
                disconnected_cb=disconnected_callback,
                reconnected_cb=reconnected_callback,
                closed_cb=closed_callback,
                **self._connection_options,
            )

            logger.info(
                "Connected to %s",
                self._nc.connected_url,
            )

            return self._nc

        except TimeoutError:
            logger.exception("Connection timed out.")
            raise

        except Error:
            logger.exception("Unable to connect to NATS.")
            raise

        except Exception:
            logger.exception("Unexpected error while connecting.")
            raise

    async def publish(
        self,
        subject: str,
        payload: bytes,
    ) -> None:
        """
        Publish a message.

        Args:
            subject:
                Subject name.

            payload:
                Message payload.
        """
        try:
            await self.connection.publish(subject, payload)
            await self.connection.flush()

            logger.info(
                "Published message to '%s'",
                subject,
            )

        except Exception:
            logger.exception("Failed to publish message.")
            raise

    async def subscribe(
        self,
        subject: str,
        callback: Callable[[Msg], Awaitable[None]],
    ):
        """
        Subscribe to a subject.

        Args:
            subject:
                Subject to subscribe.

            callback:
                Async callback for incoming messages.
        """
        try:
            subscription = await self.connection.subscribe(
                subject,
                cb=callback,
            )

            logger.info(
                "Subscribed to '%s'",
                subject,
            )

            return subscription

        except Exception:
            logger.exception("Subscription failed.")
            raise

    async def request(
        self,
        subject: str,
        payload: bytes,
        timeout: float = 2.0,
    ) -> Msg:
        """
        Send a request and wait for a reply.

        Args:
            subject:
                Request subject.

            payload:
                Request payload.

            timeout:
                Maximum wait time.

        Returns:
            Reply message.
        """
        try:
            return await self.connection.request(
                subject,
                payload,
                timeout=timeout,
            )

        except TimeoutError:
            logger.exception("Request timed out.")
            raise

    async def close(self) -> None:
        """
        Gracefully close the connection.
        """
        if self._nc is None:
            return

        try:
            if not self._nc.is_closed:
                logger.info("Closing NATS connection...")
                await self._nc.drain()

        except Exception:
            logger.exception("Error while closing connection.")
            raise

    async def wait_forever(self) -> None:
        """
        Keep the client alive until interrupted.
        """
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user.")