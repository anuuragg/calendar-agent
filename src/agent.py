import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from groq import Groq

from mcp import Client


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
   - if duration is not provided, ask the user.

5. You may add descriptions or notes to events when the user
   provides additional information.

6. Never delete an event without explicit confirmation
   from the user.

7. When moving an event, first identify the correct event
   if the user has not provided an event ID.

8. Use the calendar tools whenever calendar information
   is required.

9. After successfully performing an action,
   clearly tell the user what happened.

10. When you list or mention calendar events, output ONLY the events,
    never their descriptions or notes. Put them in one fenced block
    tagged events, containing a JSON array. Each object has: title,
    date (YYYY-MM-DD), start (HH:MM, 24h), end (HH:MM), location,
    description. Do not use tables or bullet lists for events. Do not
    write the description in your reply text. Only add one short line
    of commentary outside the block. If the user asks about one
    specific event's description, answer that in plain text.
"""


messages = [
    {
        "role": "system",
        "content": build_system_prompt(),
    }
]


def convert_mcp_tools_to_groq(mcp_tools):
    
    #Convert MCP tool definitions into the format expected by Groq's tool calling API.

    tools = []

    for tool in mcp_tools:

        tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        })

    return tools


def get_mcp_result(result):
    
    # Convert an MCP CallToolResult into a string that can be sent back to the Groq model.
    if result.structured_content:
        return json.dumps(result.structured_content)

    content = []

    for item in result.content:

        if hasattr(item, "text"):
            content.append(item.text)

        else:
            content.append(str(item))

    return "\n".join(content)


async def run_agent(
    user_input,
    mcp_client,
    groq_tools,
    max_iterations=10,
):

    # Add user message to conversation history
    messages.append({
        "role": "user",
        "content": user_input,
    })

    for iteration in range(max_iterations):

        print(f"\nIteration {iteration + 1}")

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=groq_tools,
            tool_choice="auto",
        )

        message = response.choices[0].message

        # Add assistant response to conversation history
        messages.append(
            message.model_dump(exclude_none=True)
        )

        # Agent finished
        if not message.tool_calls:

            return message.content

        # Execute MCP tool calls
        for call in message.tool_calls:

            name = call.function.name

            arguments = json.loads(
                call.function.arguments
            )

            print("\nTool call:")
            print("  Name:", name)
            print("  Arguments:", arguments)
            print("  ID:", call.id)

            try:

                # Call the tool through MCP
                result = await mcp_client.call_tool(
                    name,
                    arguments,
                )

                tool_result = get_mcp_result(result)

            except Exception as e:

                tool_result = json.dumps({
                    "error": str(e)
                })

            print("Tool result:")
            print(" ", tool_result)

            # Send MCP result back to Groq
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": tool_result,
            })

    return "I reached the maximum number of tool calls."