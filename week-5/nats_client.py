"""
nats_client.py

Centralized NATS/JetStream connection helper.

Provides a single `get_js_client()` function that all publishers/workers
use to connect, so reconnect behavior and logging are consistent everywhere.
"""

import nats

NATS_URL = "nats://localhost:4222"


async def error_cb(e):
    """
    Called whenever the NATS client encounters an async error
    (e.g., failed publish, slow consumer, subscription error).
    """
    print(f"[NATS ERROR] {e}")


async def disconnected_cb():
    """
    Called when the client loses its connection to the server.
    The client will automatically attempt to reconnect after this.
    """
    print("[NATS] Disconnected from server — attempting to reconnect...")


async def reconnected_cb():
    """
    Called after the client successfully reconnects following a disconnect.
    """
    print("[NATS] Reconnected to server successfully")


async def closed_cb():
    """
    Called when the connection is permanently closed —
    either by explicit drain()/close(), or after exhausting
    max_reconnect_attempts with no success.
    """
    print("[NATS] Connection closed permanently")


async def get_js_client():
    """
    Connect to NATS and return both the raw connection and a JetStream context.

    Configures automatic reconnection with logging callbacks so connection
    health is visible in worker/publisher logs.

    Returns:
        tuple: (nc, js)
            nc -> the raw NATS connection (use for nc.drain() / nc.close())
            js -> the JetStream context (use for publish/subscribe operations)
    """
    print(f"[NATS] Connecting to {NATS_URL}...")

    nc = await nats.connect(
        NATS_URL,
        reconnect_time_wait=2,        # seconds to wait between reconnect attempts
        max_reconnect_attempts=-1,     # -1 = retry forever, never give up
        error_cb=error_cb,
        disconnected_cb=disconnected_cb,
        reconnected_cb=reconnected_cb,
        closed_cb=closed_cb,
    )

    print("[NATS] Connected successfully")

    js = nc.jetstream()
    return nc, js