"""
worker.py

Durable pull-consumer worker for the "order.cancelled" subject.

Features:
- Automatic reconnect handling (via nats_client.get_js_client)
- Idempotent processing (dedup via Nats-Msg-Id / stream sequence)
- Dead-letter routing after max delivery attempts
- Graceful shutdown on SIGTERM/SIGINT (drains connection, finishes in-flight work)
"""

import asyncio
import signal

import nats.errors
from nats_client import get_js_client

# Event used to signal the main loop to stop pulling new messages
shutdown_event = asyncio.Event()

# In-memory idempotency cache (swap for Redis/DB in real production use —
# this resets on every restart, so it only protects against duplicates
# within a single process lifetime, not across restarts)
processed_cache = set()

SUBJECT = "order.cancelled"


async def process(msg, js):
    """
    Process a single JetStream message with idempotency and dead-letter handling.

    Args:
        msg: The NATS message to process.
        js: The JetStream client (used to publish to the DLQ subject on failure).

    Behavior:
        - Skips (but still acks) messages already seen in `processed_cache`.
        - Runs the actual business logic inside a try/except.
        - On failure, retries via nak() up to 5 delivery attempts, then
          routes the message to a dead-letter subject and terminates it.
    """
    msg_id = msg.headers.get("Nats-Msg-Id") if msg.headers else str(msg.metadata.sequence.stream)

    if msg_id in processed_cache:
        print(f"[SKIP] Message {msg_id} already processed — acking without reprocessing")
        await msg.ack()
        return

    try:
        print(f"[PROCESS] Handling message {msg_id}: {msg.data.decode()}")

        await asyncio.sleep(1)

        processed_cache.add(msg_id)
        await msg.ack()
        print(f"[ACK] Message {msg_id} processed and acknowledged")

    except Exception as e:
        print(f"[ERROR] Failed to process message {msg_id}: {e}")

        if msg.metadata.num_delivered >= 5:
            print(f"[DLQ] Message {msg_id} exceeded max delivery attempts, moving to DLQ")
            await js.publish("order.cancelled.dlq", msg.data, headers={"error": str(e)})
            await msg.term()
        else:
            print(f"[RETRY] Message {msg_id} will be retried (attempt {msg.metadata.num_delivered})")
            await msg.nak(delay=5)  # NOTE: this was missing 'await' in the original code


async def main():
    """
    Main worker entrypoint.

    Connects to NATS/JetStream, binds to the durable pull consumer
    "order-cancelled-processor" on subject "order.cancelled", and continuously
    fetches and processes messages until a shutdown signal is received.
    """
    print("[STARTUP] Connecting to NATS...")
    nc, js = await get_js_client()
    print("[STARTUP] Connected. Binding to durable consumer 'order-cancelled-processor'...")

    psub = await js.pull_subscribe(SUBJECT, durable="order-cancelled-processor")
    print("[STARTUP] Worker ready. Waiting for messages...")

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_event.set)

    while not shutdown_event.is_set():
        try:
            msgs = await psub.fetch(batch=5, timeout=5)
        except nats.errors.TimeoutError:
            # No messages available right now — normal, just loop again
            continue

        print(f"[FETCH] Received batch of {len(msgs)} message(s)")
        for msg in msgs:
            await process(msg, js)

    print("[SHUTDOWN] Shutdown signal received. Draining connection...")
    await nc.drain()
    print("[SHUTDOWN] Connection drained. Worker exited cleanly.")


if __name__ == "__main__":
    asyncio.run(main())