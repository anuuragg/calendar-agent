from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build

from auth import get_credentials


TIMEZONE = "Asia/Kolkata"


def get_calendar_service():
    creds = get_credentials()

    return build(
        "calendar",
        "v3",
        credentials=creds,
    )


def list_events(
    start_date=None,
    end_date=None,
    query=None,
):
    service = get_calendar_service()

    now = datetime.now(ZoneInfo(TIMEZONE))

    time_min = (
        datetime.fromisoformat(start_date)
        .replace(tzinfo=ZoneInfo(TIMEZONE))
        if start_date
        else now
    )

    time_max = (
        datetime.fromisoformat(end_date)
        .replace(tzinfo=ZoneInfo(TIMEZONE))
        if end_date
        else None
    )

    params = {
        "calendarId": "primary",
        "timeMin": time_min.isoformat(),
        "singleEvents": True,
        "orderBy": "startTime",
        "maxResults": 50,
    }

    if time_max:
        params["timeMax"] = time_max.isoformat()

    if query:
        params["q"] = query

    response = service.events().list(**params).execute()

    events = []

    for event in response.get("items", []):
        start = event.get("start", {})
        end = event.get("end", {})

        events.append({
            "id": event.get("id"),
            "title": event.get("summary", "Untitled"),
            "description": event.get("description", ""),
            "start": start.get("dateTime", start.get("date")),
            "end": end.get("dateTime", end.get("date")),
            "status": event.get("status"),
        })

    return events


def add_event(title, date, time, duration_minutes, description=None):
    service = get_calendar_service()

    timezone = ZoneInfo(TIMEZONE)

    start = datetime.fromisoformat(
        f"{date}T{time}"
    ).replace(tzinfo=timezone)

    end = start + timedelta(minutes=duration_minutes)

    event = {
        "summary": title,
        "description": description or "",
        "start": {
            "dateTime": start.isoformat(),
            "timeZone": TIMEZONE,
        },
        "end": {
            "dateTime": end.isoformat(),
            "timeZone": TIMEZONE,
        },
    }

    created = service.events().insert(
        calendarId="primary",
        body=event,
    ).execute()

    return {
        "success": True,
        "id": created["id"],
        "title": created.get("summary"),
        "description": created.get("description"),
        "start": created["start"].get("dateTime"),
        "end": created["end"].get("dateTime"),
    }


def move_event(event_id, date, time):
    service = get_calendar_service()

    timezone = ZoneInfo(TIMEZONE)

    new_start = datetime.fromisoformat(
        f"{date}T{time}"
    ).replace(tzinfo=timezone)

    # Get existing event so we preserve its duration
    event = service.events().get(
        calendarId="primary",
        eventId=event_id,
    ).execute()

    old_start = datetime.fromisoformat(
        event["start"]["dateTime"]
    )

    old_end = datetime.fromisoformat(
        event["end"]["dateTime"]
    )

    duration = old_end - old_start

    new_end = new_start + duration

    event["start"] = {
        "dateTime": new_start.isoformat(),
        "timeZone": TIMEZONE,
    }

    event["end"] = {
        "dateTime": new_end.isoformat(),
        "timeZone": TIMEZONE,
    }

    updated = service.events().update(
        calendarId="primary",
        eventId=event_id,
        body=event,
    ).execute()

    return {
        "success": True,
        "id": updated["id"],
        "title": updated.get("summary"),
        "start": updated["start"].get("dateTime"),
        "end": updated["end"].get("dateTime"),
    }


def remove_event(event_id):
    service = get_calendar_service()

    service.events().delete(
        calendarId="primary",
        eventId=event_id,
    ).execute()

    return {
        "success": True,
        "id": event_id,
        "message": "Event deleted successfully.",
    }