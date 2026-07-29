"""
JetStream Publisher.

This module is responsible for publishing Order events to a JetStream
stream.

Why this file exists
--------------------
A Publisher is responsible for producing events that are persisted
inside a JetStream Stream.

Unlike Core NATS publishing, JetStream publishing returns a
Publish Acknowledgement (PubAck) which confirms that the message
has been successfully stored by the server.

Concepts demonstrated
---------------------
- JetStream Publish
- Publish Acknowledgement (PubAck)
- Message Serialization
- Structured Logging
- Error Handling
- Synchronous Publishing
"""

from __future__ import annotations

import json
import logging
import random
from json import JSONDecodeError
from typing import Any

from nats.errors import (
    ConnectionClosedError,
    ConnectionReconnectingError,
    TimeoutError,
)

from config import (
    PUBLISH_TIMEOUT,
    SUBJECT,
    TOTAL_MESSAGES,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Sample Data
# ============================================================================

LAPTOPS = [
    "MacBook Pro",
    "Dell XPS 13",
    "HP Spectre x360",
    "Lenovo ThinkPad X1 Carbon",
    "Asus ZenBook 14",
    "Microsoft Surface Laptop 4",
    "Acer Swift 3",
    "Razer Blade Stealth 13",
    "LG Gram 17",
    "Samsung Galaxy Book Pro",
    "Google Pixelbook Go",
    "Huawei MateBook X Pro",
    "Alienware m15 R4",
    "MSI GS66 Stealth",
    "Toshiba Portege X30L-G",
]


def generate_order() -> dict[str, Any]:
    """
    Generate a sample order event.

    Returns:
        Dictionary containing order details.
    """

    return {
        "id": random.randint(1000, 9999),
        "name": random.choice(LAPTOPS),
        "price": random.randint(60_000, 80_000),
    }


def serialize_order(order: dict[str, Any]) -> bytes:
    """
    Serialize an order into JSON bytes.

    Args:
        order:
            Order payload.

    Returns:
        Serialized JSON bytes.

    Raises:
        ValueError:
            If serialization fails.
    """

    try:
        return json.dumps(order).encode()

    except (TypeError, ValueError) as exc:
        raise ValueError("Failed to serialize order.") from exc


async def publish_message(js, payload: bytes):
    """
    Publish a single message to JetStream.

    Args:
        js:
            JetStream context.

        payload:
            Serialized message payload.

    Returns:
        PubAck returned by JetStream.

    Raises:
        TimeoutError:
            Publish acknowledgement timeout.

        ConnectionClosedError:
            Connection closed.

        ConnectionReconnectingError:
            Client reconnecting.
    """

    return await js.publish(
        SUBJECT,
        payload,
        timeout=PUBLISH_TIMEOUT,
    )


async def publish_orders(
    js,
    total_messages: int = TOTAL_MESSAGES,
) -> dict[str, int]:
    """
    Publish multiple order events.

    Args:
        js:
            JetStream context.

        total_messages:
            Number of events to publish.

    Returns:
        Statistics containing successful and failed publishes.
    """

    logger.info("=" * 70)
    logger.info("Publishing %d Order Event(s)", total_messages)
    logger.info("Subject : %s", SUBJECT)
    logger.info("=" * 70)

    success = 0
    failed = 0

    for index in range(1, total_messages + 1):

        order = generate_order()

        try:

            payload = serialize_order(order)

            ack = await publish_message(js, payload)

            logger.info(
                "[%03d/%03d] "
                "Published | "
                "Stream=%s "
                "Seq=%d "
                "Order=%d "
                "Laptop=%s "
                "Price=%d",
                index,
                total_messages,
                ack.stream,
                ack.seq,
                order["id"],
                order["name"],
                order["price"],
            )

            success += 1

        except ValueError:

            logger.exception(
                "Failed to serialize order: %s",
                order,
            )

            failed += 1

        except TimeoutError:

            logger.warning(
                "Publish acknowledgement timed out."
            )

            failed += 1

        except ConnectionReconnectingError:

            logger.warning(
                "Connection reconnecting. Publish skipped."
            )

            failed += 1

        except ConnectionClosedError:

            logger.error(
                "Connection closed while publishing."
            )

            raise

        except JSONDecodeError:

            logger.exception(
                "Unexpected JSON error."
            )

            failed += 1

        except Exception:

            logger.exception(
                "Unexpected publisher failure."
            )

            failed += 1

    logger.info("=" * 70)
    logger.info("Publishing Complete")
    logger.info("Successful : %d", success)
    logger.info("Failed     : %d", failed)
    logger.info("=" * 70)

    return {
        "published": success,
        "failed": failed,
    }