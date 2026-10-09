"""EventHub: fans a station's events out to every open page, and keeps
this session's history so a page that connects late can catch up.

Events are the dicts ota_station.Station emits (on_event). The hub only
makes them JSON-safe (non-finite floats become None) and keeps:
  - the latest 'link' and 'level' event,
  - the conversation: message_tx, delivery, message_rx (last 500),
  - received bursts (last 300) and log lines (last 500),
  - the last two bursts' constellation points.
"""
import asyncio
import math
from collections import deque

MESSAGE_TYPES = ('message_tx', 'delivery', 'message_rx')


def json_safe(value):
    """value with every non-finite float replaced by None (JSON has no
    Infinity/NaN; a burst with no signal reports -inf dB)."""
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


class EventHub:
    def __init__(self, queue_size=1000):
        self._subscribers = set()
        self._queue_size = queue_size
        self.link = None
        self.level = None
        self.messages = deque(maxlen=500)
        self.bursts = deque(maxlen=300)
        self.logs = deque(maxlen=500)
        self.constellations = deque(maxlen=2)

    def publish(self, event):
        """Called by the station (on its event loop) for every event."""
        event = json_safe(event)
        kind = event.get('type')
        if kind == 'link':
            self.link = event
        elif kind == 'level':
            self.level = event
        elif kind in MESSAGE_TYPES:
            self.messages.append(event)
        elif kind == 'burst_rx':
            self.bursts.append(event)
        elif kind == 'log':
            self.logs.append(event)
        elif kind == 'constellation':
            self.constellations.append(event)
        for queue in list(self._subscribers):
            if queue.full():      # a page that stopped reading: drop its oldest
                queue.get_nowait()
            queue.put_nowait(event)

    def snapshot(self, link_state=None):
        """What a newly connected page needs to draw the current state."""
        return json_safe({'type': 'snapshot', 'link': link_state or self.link,
                          'level': self.level, 'messages': list(self.messages),
                          'bursts': list(self.bursts), 'logs': list(self.logs),
                          'constellations': list(self.constellations)})

    def subscribe(self):
        queue = asyncio.Queue(maxsize=self._queue_size)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue):
        self._subscribers.discard(queue)

    @property
    def subscriber_count(self):
        return len(self._subscribers)
