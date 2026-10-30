"""External events are facts; individuals form their own memories of them."""

from .models import Event, World


def emit(world: World, **details) -> Event:
    event = Event(id=f"event-{world.next_event_id}", tick=world.tick, **details)
    world.next_event_id += 1
    world.events.append(event)
    if len(world.events) > 400:
        del world.events[0]
    world.pending_events.append(event)
    return event
