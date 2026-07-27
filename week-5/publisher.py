"""
publisher.py
Publishes messages to a JetStream stream.
Run standalone: python publisher.py
"""

import asyncio
import json
import uuid
from nats.errors import TimeoutError as NatsTimeoutError
from nats_client import get_js_client



SUBJECT = "order.cancelled"


async def publish_one(js, payload: dict, msg_id: str | None = None):
    """
    Publish a single message.
    msg_id enables JetStream's built-in de-duplication (Nats-Msg-Id header) —
    if the same msg_id is published again within the stream's duplicate window,
    it will be recognized as a duplicate and not stored twice.
    """
    data = json.dumps(payload).encode()
    headers = {"Nats-Msg-Id": msg_id} if msg_id else None

    ack = await js.publish(SUBJECT, data, headers=headers)
    print(f"Published seq={ack.seq} duplicate={ack.duplicate} payload={payload}")
    return ack


async def publish_many(js, count: int = 10):
    """Publish several messages concurrently (simulates multiple publishers)."""
    tasks = []
    for i in range(count):
        payload = {"order_id": str(uuid.uuid4()), "index": i}
        # Use order_id as msg_id so accidental republishes are deduped
        tasks.append(publish_one(js, payload, msg_id=payload["order_id"]))
    await asyncio.gather(*tasks)


async def main():
    nc,js=await get_js_client()

    try:
        await publish_many(js, count=50)
    except NatsTimeoutError:
        print("Publish timed out — stream may be unreachable or overloaded")
    finally:
        await nc.drain()

if __name__ == "__main__":
    asyncio.run(main())