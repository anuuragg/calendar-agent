import json
import os

from dotenv import load_dotenv
from groq import Groq

from tools import (
    list_events,
    add_event,
    move_event,
    remove_event,
)

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# Tool declarations

tools = [
    {
        "type": "function",
        "function": {
            "name": "list_events",
            "description": "Lists all events in the calendar.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_event",
            "description": "Adds a new event to the calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the event.",
                    },
                    "date": {
                        "type": "string",
                        "description": "The event date in YYYY-MM-DD format.",
                    },
                    "time": {
                        "type": "string",
                        "description": "The event time in HH:MM format.",
                    },
                },
                "required": ["title", "date", "time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_event",
            "description": "Moves an existing event to a new date and time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "The ID of the event to move.",
                    },
                    "date": {
                        "type": "string",
                        "description": "The new date in YYYY-MM-DD format.",
                    },
                    "time": {
                        "type": "string",
                        "description": "The new time in HH:MM format.",
                    },
                },
                "required": ["event_id", "date", "time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_event",
            "description": "Removes an event from the calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "The ID of the event to remove.",
                    },
                },
                "required": ["event_id"],
            },
        },
    },
]


tool_functions = {
    "list_events": list_events,
    "add_event": add_event,
    "move_event": move_event,
    "remove_event": remove_event,
}


# Agent
def run_agent(user_input, max_iterations=10):

    messages = [
        {
            "role": "user",
            "content": user_input,
        }
    ]

    for iteration in range(max_iterations):

        print(f"\nIteration {iteration + 1}")

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message

        # Add assistant response to history
        messages.append(message.model_dump(exclude_none=True))

        # No tool calls means we have the final answer
        if not message.tool_calls:

            print("\nFinal answer:")
            print(message.content)

            return

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

            # Send tool result back to model
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            })

    print("\nAgent stopped: maximum iterations reached.")


if __name__ == "__main__":
    user_input = input("You: ")
    run_agent(user_input)