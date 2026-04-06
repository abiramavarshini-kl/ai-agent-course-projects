# ### Welcome to Week 6 Day 3!
#
# Let's experiment with a bunch more MCP Servers

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from datetime import datetime

load_dotenv(override=True)


# ### The first type of MCP Server: runs locally, everything local
#
# Knowledge-graph based persistent memory.
# https://github.com/modelcontextprotocol/servers/tree/main/src/memory

async def memory_demo():
    # Build an absolute path that works on Windows (forward slashes required for libSQL)
    db_path = Path(__file__).parent / "memory" / "ed.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    libsql_url = "file:" + db_path.as_posix()  # e.g. file:C:/Users/Abi/projects/agents/6_mcp/memory/ed.db

    params = {
        "command": "npx",
        "args": ["-y", "mcp-memory-libsql"],
        "env": {"LIBSQL_URL": libsql_url}
    }

    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
        mcp_tools = await server.list_tools()
    print(mcp_tools)

    instructions = "You use your entity tools as a persistent memory to store and recall information about your conversations."
    request = (
        "My name's Ed. I'm an LLM engineer. I'm teaching a course about AI Agents, "
        "including the incredible MCP protocol. MCP is a protocol for connecting agents "
        "with tools, resources and prompt templates, and makes it easy to integrate AI "
        "agents with capabilities."
    )
    model = "gpt-4.1-mini"

    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
        agent = Agent(name="agent", instructions=instructions, model=model, mcp_servers=[mcp_server])
        with trace("conversation"):
            result = await Runner.run(agent, request)
        print(result.final_output)

    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
        agent = Agent(name="agent", instructions=instructions, model=model, mcp_servers=[mcp_server])
        with trace("conversation"):
            result = await Runner.run(agent, "My name's Ed. What do you know about me?")
        print(result.final_output)


# ### The 2nd type of MCP server - runs locally, calls a web service
#
# Using Serper Search (https://serper.dev)
# Sign up for a free key and add it to .env as: SERPER_API_KEY=xxxx

async def search_demo():
    env = {"SERPER_API_KEY": os.getenv("SERPER_API_KEY")}
    params = {"command": "npx", "args": ["-y", "serper-search-scrape-mcp-server"], "env": env}

    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
        mcp_tools = await server.list_tools()
    print(mcp_tools)

    instructions = "You are able to search the web for information and briefly summarize the takeaways."
    request = (
        f"Please research the latest news on Amazon stock price and briefly summarize its outlook. "
        f"For context, the current date is {datetime.now().strftime('%Y-%m-%d')}"
    )
    model = "gpt-4o-mini"

    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
        agent = Agent(name="agent", instructions=instructions, model=model, mcp_servers=[mcp_server])
        with trace("conversation"):
            result = await Runner.run(agent, request)
        print(result.final_output)


# ### Polygon.io MCP Server
# Sign up at https://polygon.io and add your key to .env as: POLYGON_API_KEY=xxxx

async def polygon_demo():
    load_dotenv(override=True)
    polygon_api_key = os.getenv("POLYGON_API_KEY")
    if not polygon_api_key:
        print("POLYGON_API_KEY is not set")
        return

    from polygon import RESTClient
    client = RESTClient(polygon_api_key)
    print(client.get_previous_close_agg("AAPL")[0])

    from market import get_share_price
    print(get_share_price("AAPL"))

    # No rate limiting concerns!
    for i in range(1000):
        get_share_price("AAPL")
    print(get_share_price("AAPL"))

    market_server_path = str(Path(__file__).parent / "market_server.py")
    params = {"command": "uv", "args": ["run", market_server_path]}
    async with MCPServerStdio(params=params, client_session_timeout_seconds=60) as server:
        mcp_tools = await server.list_tools()
    print(mcp_tools)

    instructions = "You answer questions about the stock market."
    request = "What's the share price of Apple?"
    model = "gpt-4.1-mini"

    async with MCPServerStdio(params=params, client_session_timeout_seconds=60) as mcp_server:
        agent = Agent(name="agent", instructions=instructions, model=model, mcp_servers=[mcp_server])
        with trace("conversation"):
            result = await Runner.run(agent, request)
        print(result.final_output)

    # Polygon.io Part 2: Paid Plan (Optional)
    params = {
        "command": "uvx",
        "args": ["--from", "git+https://github.com/polygon-io/mcp_polygon@v0.1.0", "mcp_polygon"],
        "env": {"POLYGON_API_KEY": polygon_api_key}
    }
    async with MCPServerStdio(params=params, client_session_timeout_seconds=60) as server:
        mcp_tools = await server.list_tools()
    print(mcp_tools)

    instructions = "You answer questions about the stock market."
    request = "What's the share price of Apple? Use your get_snapshot_ticker tool to get the latest price."
    model = "gpt-4.1-mini"

    async with MCPServerStdio(params=params, client_session_timeout_seconds=60) as mcp_server:
        agent = Agent(name="agent", instructions=instructions, model=model, mcp_servers=[mcp_server])
        with trace("conversation"):
            result = await Runner.run(agent, request)
        print(result.final_output)

    polygon_plan = os.getenv("POLYGON_PLAN")
    if polygon_plan == "paid":
        print("You've chosen the paid Polygon plan — prices on a 15 min delay.")
    elif polygon_plan == "realtime":
        print("Wowzer - you've chosen the realtime Polygon plan!")
    else:
        print("Using the free Polygon plan — EOD prices.")


async def main():
    await memory_demo()
    await search_demo()
    await polygon_demo()


if __name__ == "__main__":
    asyncio.run(main())