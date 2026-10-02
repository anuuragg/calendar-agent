from datetime import datetime


# Fake in-memory calendar
events = [
    {
        "id": "1",
        "title": "DBT Meeting",
        "date": "2026-10-03",
        "time": "10:00",
    },
    {
        "id": "2",
        "title": "Gym",
        "date": "2026-10-03",
        "time": "18:00",
    },
]


def list_events():
    return events


def add_event(title, date, time):
    event = {
        "id": str(len(events) + 1),
        "title": title,
        "date": date,
        "time": time,
    }

    events.append(event)

    return event


def move_event(event_id, date, time):
    for event in events:
        if event["id"] == event_id:
            event["date"] = date
            event["time"] = time

            return event

        return {
            "error": f"Event with id {event_id} not found"
        }


def remove_event(event_id):
    for event in events:
        if event["id"] == event_id:
            events.remove(event)

            return {
                "success": True,
                "removed_event": event,
            }

    return {
        "error": f"Event with id {event_id} not found"
    }