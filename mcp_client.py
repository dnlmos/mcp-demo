import asyncio
import sys
from builtins import print

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from utils import spinner

try:
    from rich import print
except ImportError:
    pass


async def tools(mcp_tools):
    tools = await mcp_tools.to_tool_list_async()
    for tool in tools:
        print(tool.metadata.name, tool.metadata.description)


async def chat_loop(agent):
    print("[bold green]🤖 MCP Agent Ready![/bold green]")
    print(
        "Type your message and press Enter. Type [yellow]'exit'[/yellow] or press Ctrl+C to quit.\n"
    )
    messages = []
    try:
        while True:
            try:
                user_prompt = input("📝 Your prompt: ").strip()
            except EOFError:
                break  # handle Ctrl+D
            if not user_prompt:
                continue
            if user_prompt.lower() in {"exit", "quit"}:
                print("[bold red]👋 Goodbye![/bold red]")
                break

            spinner_task = asyncio.create_task(
                spinner("Waiting for response...")
            )
            try:
                result = await agent.run(user_prompt, message_history=messages)
                print(
                    "[bold magenta]Agent[/bold magenta]:",
                    result.output,
                )
                messages = result.all_messages()
            except Exception as e:
                print(f"[bold red]⚠️ Error:[/bold red] {e}")

            finally:
                spinner_task.cancel()
                try:
                    await spinner_task
                except asyncio.CancelledError:
                    pass

    except KeyboardInterrupt:
        print("\n[bold red]👋 Goodbye![/bold red]")
        sys.exit(0)


async def main():
    server = MCPServerSSE(url="http://127.0.0.1:8000/sse")
    ollama_model = OpenAIChatModel(
        model_name="hf.co/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF:Q4_K_M",
        provider=OllamaProvider(base_url="http://localhost:11434/v1"),
    )
    agent = Agent(
        ollama_model,
        toolsets=[server],
        system_prompt="You are an AI assistant for Tool Calling. Before you help a user, you need to work with tools to interact with our Database or help user with filesystem, reading directories.",
    )
    await chat_loop(agent)


if __name__ == "__main__":
    asyncio.run(main())
