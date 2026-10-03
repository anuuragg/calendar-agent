import json
import sys
from pathlib import Path

from mcp.server import MCPServer
from mcp.types import TextContent


ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"

sys.path.insert(0, str(SRC_DIR))


from google_calendar import (
    list_events as calendar_list_events,
    add_event as calendar_add_event,
    move_event as calendar_move_event,
    remove_event as calendar_remove_event,
)


mcp = MCPServer("Google Calendar")


@mcp.tool()
def list_events(
    start_date: str | None = None,
    end_date: str | None = None,
    query: str | None = None,
) -> list[TextContent]:

    events = calendar_list_events(
        start_date=start_date,
        end_date=end_date,
        query=query,
    )

    return [
        TextContent(
            type="text",
            text=json.dumps(events),
        )
    ]


@mcp.tool()
def add_event(
    title: str,
    date: str,
    time: str,
    duration_minutes: int,
    description: str | None = None,
) -> list[TextContent]:

    result = calendar_add_event(
        title=title,
        date=date,
        time=time,
        duration_minutes=duration_minutes,
        description=description,
    )

    return [
        TextContent(
            type="text",
            text=json.dumps(result),
        )
    ]


@mcp.tool()
def move_event(
    event_id: str,
    date: str,
    time: str,
) -> list[TextContent]:

    result = calendar_move_event(
        event_id=event_id,
        date=date,
        time=time,
    )

    return [
        TextContent(
            type="text",
            text=json.dumps(result),
        )
    ]


@mcp.tool()
def remove_event(
    event_id: str,
) -> list[TextContent]:

    result = calendar_remove_event(
        event_id=event_id,
    )

    return [
        TextContent(
            type="text",
            text=json.dumps(result),
        )
    ]


if __name__ == "__main__":
    mcp.run()