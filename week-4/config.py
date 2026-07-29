"""
Application configuration.

This module contains all configuration values used throughout the
JetStream learning project.

Why this file exists
--------------------
Instead of scattering configuration values throughout the project,
they are centralized here. This makes the application easier to
maintain, configure, and understand.

Concepts demonstrated
---------------------
- Centralized configuration
- Constants
- Avoiding magic values
- Reusable configuration
"""

from __future__ import annotations

# ============================================================================
# NATS SERVER
# ============================================================================

#: NATS server connection URL.
NATS_URL: str = "nats://localhost:4222"

#: Client name displayed in the NATS monitoring endpoints.
CLIENT_NAME: str = "order-service"

# ============================================================================
# JETSTREAM
# ============================================================================

#: Stream that stores all order events.
STREAM: str = "ORDERS"

#: Subject published by the producer.
SUBJECT: str = "order.created"

#: Durable consumer name.
DURABLE: str = "order-created-processor"

# ============================================================================
# PUBLISHER
# ============================================================================

#: Number of messages published during a demo run.
TOTAL_MESSAGES: int = 500

#: Timeout while waiting for a publish acknowledgement.
PUBLISH_TIMEOUT: int = 5

# ============================================================================
# WORKER
# ============================================================================

#: Number of messages fetched in one pull request.
FETCH_BATCH_SIZE: int = 5

#: Time to wait for new messages.
FETCH_TIMEOUT: int = 5

#: Simulated business processing time.
PROCESSING_DELAY: int = 2

#: Delay before polling again when no messages are available.
POLL_DELAY: int = 1

#: Delay before retrying after reconnect.
RECONNECT_DELAY: int = 2

#: Delay before retrying failed messages.
NAK_DELAY: int = 5

#: Delay before retrying temporary business failures.
RETRY_DELAY: int = 10

# ============================================================================
# CONNECTION
# ============================================================================

#: Connection timeout.
CONNECT_TIMEOUT: int = 5

#: Seconds to wait before reconnecting.
RECONNECT_WAIT: int = 2

#: Infinite reconnect attempts.
MAX_RECONNECT_ATTEMPTS: int = -1