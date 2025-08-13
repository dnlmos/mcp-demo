import asyncio
import sys

try:
    from rich import print
except ImportError:
    from builtins import print

from llama_index.core import Settings
from llama_index.core.agent.workflow import (
    FunctionAgent,
    ToolCall,
    ToolCallResult,
)
from llama_index.core.workflow import Context
from llama_index.llms.ollama import Ollama
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

from utils import spinner


async def handle_user_message(
    message_content: str,
    agent: FunctionAgent,
    agent_context: Context,
    verbose: bool = False,
):
    spinner_task = asyncio.create_task(spinner("Waiting for response..."))

    try:
        handler = agent.run(message_content, ctx=agent_context)
        async for event in handler.stream_events():
            if verbose and type(event) == ToolCall:
                print(
                    f"Calling tool {event.tool_name} with kwargs {event.tool_kwargs}"
                )
            elif verbose and type(event) == ToolCallResult:
                print(f"Tool {event.tool_name} returned {event.tool_output}")

        response = await handler
        return str(response)
    except Exception as e:
        print(f"⚠️ Error occurred: {e}")
    finally:
        spinner_task.cancel()
        try:
            await spinner_task
        except asyncio.CancelledError:
            pass


async def get_agent(tools, llm):
    tools = await tools.to_tool_list_async()
    agent = FunctionAgent(
        name="Agent",
        description="An agent that can work with Our Database software.",
        llm=llm,
        tools=tools,
        system_prompt="""\
            You are an AI assistant for Tool Calling.
            Before you help a user, you need to work with tools to interact with our Database or help user with filesystem, reading directories.
            """,
    )
    return agent


async def tools(mcp_tools):
    tools = await mcp_tools.to_tool_list_async()
    for tool in tools:
        print(tool.metadata.name, tool.metadata.description)


async def chat_loop(agent, agent_context):
    print("[bold green]🤖 MCP Agent Ready![/bold green]")
    print(
        "Type your message and press Enter. Type [yellow]'exit'[/yellow] or press Ctrl+C to quit.\n"
    )

    try:
        while True:
            try:
                user_input = input("📝 Your prompt: ").strip()
            except EOFError:
                break  # handle Ctrl+D

            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("[bold red]👋 Goodbye![/bold red]")
                break

            try:
                response = await handle_user_message(
                    user_input, agent, agent_context, verbose=False
                )
                print("[bold magenta]Agent[/bold magenta]:", response)
            except Exception as e:
                print(f"[bold red]⚠️ Error:[/bold red] {e}")

    except KeyboardInterrupt:
        print("\n[bold red]👋 Goodbye![/bold red]")
        sys.exit(0)


async def main():
    llm = Ollama(
        model="hf.co/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF:Q4_K_M",
        request_timeout=120.0,
    )
    Settings.llm = llm

    mcp_client = BasicMCPClient("http://127.0.0.1:8000/sse")
    mcp_tools = McpToolSpec(
        client=mcp_client
    )  # you can also pass list of allowed tools
    agent = await get_agent(mcp_tools, llm)
    agent_context = Context(agent)
    await tools(mcp_tools)

    await chat_loop(agent, agent_context)


if __name__ == "__main__":
    asyncio.run(main())
