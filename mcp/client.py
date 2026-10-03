import asyncio
from pathlib import Path

from mcp import Client, StdioServerParameters


ROOT_DIR = Path(__file__).resolve().parent.parent

server_params = StdioServerParameters(
    command="python",
    args=[
        str(ROOT_DIR / "mcp" / "server.py"),
    ],
)


async def main():

    async with Client(server_params) as client:

        print("Connected to MCP server.\n")

        result = await client.list_tools()

        print("Available tools:")

        for tool in result.tools:
            print(f"- {tool.name}")

        print()

        result = await client.call_tool(
            "list_events",
            {},
        )

        print("list_events result:")

        if result.structured_content:
            print(result.structured_content)
        else:
            for content in result.content:
                print(content)


if __name__ == "__main__":
    asyncio.run(main())