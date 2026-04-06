import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio

load_dotenv(override=True)


async def main():

    from accounts import Account

    account = Account.get("Ed")
    print(account)

    account.buy_shares("AMZN", 3, "Because this bookstore website looks promising")

    account.report()

    account.list_transactions()


    # ### Now we write an MCP server and use it directly!

    # Now let's use our accounts server as an MCP server
    params = {"command": "uv", "args": ["run", "6_mcp/accounts_server.py"]}
    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as server:
        mcp_tools = await server.list_tools()

    print(mcp_tools)

    instructions = "You are able to manage an account for a client, and answer questions about the account."
    request = "My name is Ed and my account is under the name Ed. What's my balance and my holdings?"
    model = "gpt-4.1-mini"

    try:
        async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
            agent = Agent(name="account_manager", instructions=instructions, model=model, mcp_servers=[mcp_server])
            with trace("account_manager"):
                result = await Runner.run(agent, request)
            print(result.final_output)
    except Exception as e:
        print(f"Error in MCP server: {e}")


    # ### Now let's build our own MCP Client

    from accounts_client import get_accounts_tools_openai, read_accounts_resource, list_accounts_tools

    mcp_tools = await list_accounts_tools()
    print(mcp_tools)
    openai_tools = await get_accounts_tools_openai()
    print(openai_tools)

    request = "My name is Ed and my account is under the name Ed. What's my balance?"

    with trace("account_mcp_client"):
        agent = Agent(name="account_manager", instructions=instructions, model=model, tools=openai_tools)
        result = await Runner.run(agent, request)
        print(result.final_output)

    context = await read_accounts_resource("ed")
    print(context)

    Account.get("ed").report()


    # ### Exercises
    #
    # Make your own MCP Server! Make a simple function to return the current Date,
    # and expose it as a tool so that an Agent can tell you today's date.
    #
    # Harder optional exercise: then make an MCP Client, and use a native OpenAI call
    # (without the Agents SDK) to use your tool via your client.


if __name__ == "__main__":
    asyncio.run(main())