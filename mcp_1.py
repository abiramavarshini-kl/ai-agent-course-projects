import asyncio
import sys
import os
from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio

# Windows fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


async def main():
    load_dotenv(override=True)

    # --- Fetch tools ---
    fetch_params = {"command": "uvx", "args": ["mcp-server-fetch"]}

    async with MCPServerStdio(params=fetch_params, client_session_timeout_seconds=60) as server:
        fetch_tools = await server.list_tools()
        print("Fetch tools:", fetch_tools)

    # --- Playwright tools ---
    playwright_params = {"command": "npx", "args": ["@playwright/mcp@latest"]}

    async with MCPServerStdio(params=playwright_params, client_session_timeout_seconds=60) as server:
        playwright_tools = await server.list_tools()
        print("Playwright tools:", playwright_tools)

    # --- File system tools ---
    sandbox_path = os.path.abspath(os.path.join(os.getcwd(), "sandbox"))
    files_params = {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", sandbox_path],
    }

    async with MCPServerStdio(params=files_params, client_session_timeout_seconds=60) as server:
        file_tools = await server.list_tools()
        print("File tools:", file_tools)

    # --- Agent Instructions ---
    instructions = """
    You browse the internet to accomplish your instructions.
    You are highly capable at browsing the internet independently to accomplish your task,
    including accepting all cookies and clicking 'not now' as appropriate.
    If one website isn't fruitful, try another.
    Be persistent until you have solved your assignment.
    When you need to write files, you do that inside the sandbox folder only.
    """

    # --- Run Agent ---
    async with MCPServerStdio(params=files_params, client_session_timeout_seconds=60) as mcp_server_files:
        async with MCPServerStdio(params=playwright_params, client_session_timeout_seconds=60) as mcp_server_browser:

            agent = Agent(
                name="investigator",
                instructions=instructions,
                model="gpt-4.1-mini",
                mcp_servers=[mcp_server_files, mcp_server_browser],
            )

            with trace("investigate"):
                result = await Runner.run(
                    agent,
                    "Find a great recipe for Banoffee Pie, then summarize it in markdown to banoffee.md",
                    max_turns=30
                )
                print(result.final_output)


# Run the async program
if __name__ == "__main__":
    asyncio.run(main())