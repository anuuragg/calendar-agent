import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from groq import Groq

from tools import tool_functions


load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = "openai/gpt-oss-120b"
TIMEZONE = "Asia/Kolkata"


def get_current_datetime():
    now = datetime.now(ZoneInfo(TIMEZONE))

    return now.strftime("%Y-%m-%d %H:%M:%S")


def build_system_prompt():
    now = get_current_datetime()

    return f"""
You are a personal Google Calendar assistant.

Current date and time:
{now}

Timezone:
{TIMEZONE}

Rules:

1. Always interpret dates and times using the current date,
   current time, and timezone provided above.

2. Never guess an ambiguous event.

3. If multiple events could match a request,
   show the matching events and ask the user which one they mean.

4. When creating an event:
   - determine the correct date
   - determine the start time
   - determine the duration
   - if the duration is not provided, ask the user.

5. Never delete an event without explicit confirmation
   from the user.

6. When moving an event, first identify the correct event
   if the user has not provided an event ID.

7. Use the calendar tools whenever calendar information
   is required.

8. After successfully performing an action,
   clearly tell the user what happened.
"""


tools = [
    {
        "type": "function",
        "function": {
            "name": "list_events",
            "description": (
                "List events from Google Calendar. "
                "Use this when you need to inspect existing events "
                "or find events matching a user's request."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": (
                            "Start date/time in ISO format. "
                            "Example: 2026-10-03T00:00:00"
                        ),
                    },
                    "end_date": {
                        "type": "string",
                        "description": (
                            "End date/time in ISO format. "
                            "Example: 2026-10-04T00:00:00"
                        ),
                    },
                    "query": {
                        "type": "string",
                        "description": (
                            "Optional text search for an event title, "
                            "description, location, etc."
                        ),
                    },
                },
                "required": [],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "add_event",
            "description": "Create a new Google Calendar event.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Event title.",
                    },
                    "date": {
                        "type": "string",
                        "description": "Event date in YYYY-MM-DD format.",
                    },
                    "time": {
                        "type": "string",
                        "description": "Event start time in HH:MM format.",
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": (
                            "Duration of the event in minutes."
                        ),
                    },
                },
                "required": [
                    "title",
                    "date",
                    "time",
                    "duration_minutes",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "move_event",
            "description": (
                "Move an existing Google Calendar event "
                "to a new date and time."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "Google Calendar event ID.",
                    },
                    "date": {
                        "type": "string",
                        "description": "New date in YYYY-MM-DD format.",
                    },
                    "time": {
                        "type": "string",
                        "description": "New start time in HH:MM format.",
                    },
                },
                "required": [
                    "event_id",
                    "date",
                    "time",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "remove_event",
            "description": (
                "Delete an event from Google Calendar. "
                "NEVER use this unless the user has explicitly "
                "confirmed that the event should be deleted."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "Google Calendar event ID.",
                    },
                },
                "required": ["event_id"],
            },
        },
    },
]


def run_agent(user_input, max_iterations=10):

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(),
        },
        {
            "role": "user",
            "content": user_input,
        },
    ]

    for iteration in range(max_iterations):

        print(f"\nIteration {iteration + 1}")

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message

        # Add assistant's response to conversation history
        messages.append(
            message.model_dump(exclude_none=True)
        )

        # Agent finished
        if not message.tool_calls:

            print("\nFinal answer:")
            print(message.content)

            return message.content

        
        # Execute tool calls
        for call in message.tool_calls:

            name = call.function.name

            arguments = json.loads(
                call.function.arguments
            )

            print("\nTool call:")
            print("  Name:", name)
            print("  Arguments:", arguments)
            print("  ID:", call.id)

            function = tool_functions.get(name)

            if function is None:

                result = {
                    "error": f"Unknown tool: {name}"
                }

            else:

                try:
                    result = function(**arguments)

                except Exception as e:

                    result = {
                        "error": str(e)
                    }

            print("Tool result:")
            print(" ", result)

            # Send tool result back to the model
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            })

    print(
        "\nAgent stopped: maximum iterations reached."
    )

    return None


if __name__ == "__main__":
    user_input = input("You: ")
    run_agent(user_input)