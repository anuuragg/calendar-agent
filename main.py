import json
import os

from dotenv import load_dotenv
from google import genai

from tools import (
    list_events,
    add_event,
    move_event,
    remove_event,
)


load_dotenv()

client = genai.Client(
    api_key=os.getenv("API_KEY")
)

# Tool declarations

list_events_tool = {
    "type": "function",
    "name": "list_events",
    "description": "Lists all events in the calendar.",
}


add_event_tool = {
    "type": "function",
    "name": "add_event",
    "description": "Adds a new event to the calendar.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The title of the event."
            },
            "date": {
                "type": "string",
                "description": "The event date in YYYY-MM-DD format."
            },
            "time": {
                "type": "string",
                "description": "The event time in HH:MM format."
            },
        },
        "required": ["title", "date", "time"],
    },
}


move_event_tool = {
    "type": "function",
    "name": "move_event",
    "description": "Moves an existing event to a new date and time.",
    "parameters": {
        "type": "object",
        "properties": {
            "event_id": {
                "type": "string",
                "description": "The ID of the event to move."
            },
            "date": {
                "type": "string",
                "description": "The new date in YYYY-MM-DD format."
            },
            "time": {
                "type": "string",
                "description": "The new time in HH:MM format."
            },
        },
        "required": ["event_id", "date", "time"],
    },
}


remove_event_tool = {
    "type": "function",
    "name": "remove_event",
    "description": "Removes an event from the calendar.",
    "parameters": {
        "type": "object",
        "properties": {
            "event_id": {
                "type": "string",
                "description": "The ID of the event to remove."
            },
        },
        "required": ["event_id"],
    },
}


tools = [
    list_events_tool,
    add_event_tool,
    move_event_tool,
    remove_event_tool,
]


tool_functions = {
    "list_events": list_events,
    "add_event": add_event,
    "move_event": move_event,
    "remove_event": remove_event,
}


# Agent
def run_agent(user_input, max_iterations=10):

    history = [
        {
            "type": "user_input",
            "content": [
                {
                    "type": "text",
                    "text": user_input,
                }
            ],
        }
    ]

    for iteration in range(max_iterations):

        print(f"\nIteration {iteration + 1}")

        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            store=False,
            input=history,
            tools=tools,
        )

        for step in interaction.steps:
            history.append(step.model_dump())


        function_calls = [
            step
            for step in interaction.steps
            if step.type == "function_call"
        ]

        if not function_calls:
            print("\nFinal answer:")
            print(interaction.output_text)
            return


        for call in function_calls:

            print("\nTool call:")
            print("  Name:", call.name)
            print("  Arguments:", call.arguments)
            print("  ID:", call.id)

            function = tool_functions.get(call.name)

            if function is None:
                result = {
                    "error": f"Unknown tool: {call.name}"
                }
            else:
                try:
                    result = function(**call.arguments)
                except Exception as e:
                    result = {
                        "error": str(e)
                    }

            print("Tool result:")
            print(" ", result)



            history.append({
                "type": "function_result",
                "name": call.name,
                "call_id": call.id,
                "result": [
                    {
                        "type": "text",
                        "text": json.dumps(result),
                    }
                ],
            })

    print("\nAgent stopped: maximum iterations reached.")


if __name__ == "__main__":
    user_input = input("You: ")
    run_agent(user_input)