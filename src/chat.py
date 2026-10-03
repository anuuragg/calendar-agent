import asyncio
from pathlib import Path

from mcp import Client, StdioServerParameters

from agent import run_agent, convert_mcp_tools_to_groq


ROOT_DIR = Path(__file__).resolve().parent.parent

server_params = StdioServerParameters(
    command="python",
    args=[
        str(ROOT_DIR / "mcp" / "server.py"),
    ],
)


async def main():

    # Connect to MCP server
    async with Client(server_params) as mcp_client:

        print("Connected to MCP server.\n")

        # Discover tools from MCP server
        result = await mcp_client.list_tools()

        print("Available MCP tools:")

        for tool in result.tools:
            print(f"- {tool.name}")

        print()

        # Convert MCP tools to Groq format
        groq_tools = convert_mcp_tools_to_groq(
            result.tools
        )

        print("Calendar Agent")
        print("Type 'exit' or 'quit' to stop.\n")

        # Continuous chat
        while True:

            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break

            response = await run_agent(
                user_input,
                mcp_client,
                groq_tools,
            )

            if response:
                print(f"\nAgent: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())