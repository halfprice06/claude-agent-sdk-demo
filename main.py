"""
Claude Agent SDK Demo

Examples:
1. Basic query
2. Built-in tools
3. Multi-turn conversation
4. Custom tools via MCP
5. Subagents

Usage: uv run main.py
Requires: ANTHROPIC_API_KEY environment variable
"""

import asyncio
from typing import Any

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    AgentDefinition,
)


async def example_basic_query():
    """Send a prompt and stream the response."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Query")
    print("=" * 60)

    async with ClaudeSDKClient(
        options=ClaudeAgentOptions(allowed_tools=[])
    ) as client:
        await client.query("What is 2 + 2? Answer in one sentence.")

        async for message in client.receive_response():
            if isinstance(message, ResultMessage):
                print(f"\nDone. Cost: ${message.total_cost_usd:.4f}")
            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)


async def example_with_tools():
    """Use built-in tools (Glob, Read, Bash, etc.)."""
    print("\n" + "=" * 60)
    print("Example 2: Built-in Tools")
    print("=" * 60)

    async with ClaudeSDKClient(
        options=ClaudeAgentOptions(
            allowed_tools=["Glob", "Read"],
            permission_mode="bypassPermissions",
            cwd=".",
        )
    ) as client:
        await client.query("List the Python files in the current directory.")

        async for message in client.receive_response():
            if isinstance(message, ResultMessage):
                print(f"\nDone. Turns: {message.num_turns}")
            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                    elif isinstance(block, ToolUseBlock):
                        print(f"[tool] {block.name}")
                    elif isinstance(block, ToolResultBlock):
                        print(f"[result] {str(block.content)[:200]}...")


async def example_session_continuation():
    """Multi-turn conversation with context retention."""
    print("\n" + "=" * 60)
    print("Example 3: Multi-turn Conversation")
    print("=" * 60)

    async with ClaudeSDKClient(
        options=ClaudeAgentOptions(
            allowed_tools=["Glob"],
            permission_mode="bypassPermissions",
        )
    ) as client:
        print("\n--- Turn 1 ---")
        await client.query("What Python files are in this directory?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)

        print("\n--- Turn 2 ---")
        await client.query("Which one is the main entry point?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)


# Custom tool definitions

@tool(name="calculate", description="Evaluate a math expression", input_schema={"expression": str})
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a mathematical expression."""
    try:
        result = eval(args["expression"], {"__builtins__": {}}, {})
        return {"content": [{"type": "text", "text": f"Result: {result}"}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Error: {e}"}], "is_error": True}


@tool(name="greet", description="Generate a greeting", input_schema={"name": str, "style": str})
async def greet(args: dict[str, Any]) -> dict[str, Any]:
    """Generate a greeting in different styles."""
    name = args["name"]
    style = args.get("style", "friendly")
    greetings = {
        "friendly": f"Hey {name}! Great to see you!",
        "formal": f"Good day, {name}. How may I assist you?",
        "pirate": f"Ahoy, {name}! Welcome aboard, matey!",
    }
    return {"content": [{"type": "text", "text": greetings.get(style, greetings["friendly"])}]}


async def example_custom_tools():
    """Create and use custom tools via MCP."""
    print("\n" + "=" * 60)
    print("Example 4: Custom Tools via MCP")
    print("=" * 60)

    server = create_sdk_mcp_server(name="my_tools", tools=[calculate, greet])

    try:
        async with ClaudeSDKClient(
            options=ClaudeAgentOptions(
                mcp_servers={"my_tools": server},
                allowed_tools=["mcp__my_tools__calculate", "mcp__my_tools__greet"],
            )
        ) as client:
            await client.query("Calculate 15 * 7, then greet Captain Jack in pirate style.")

            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    print("\nDone.")
                elif isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(block.text)
                        elif isinstance(block, ToolUseBlock):
                            print(f"[tool] {block.name}({block.input})")
    except Exception as e:
        print(f"Error: {type(e).__name__} (in-process MCP servers can have transport issues)")


async def example_subagents():
    """Delegate work to specialized subagents."""
    print("\n" + "=" * 60)
    print("Example 5: Subagents")
    print("=" * 60)

    async with ClaudeSDKClient(
        options=ClaudeAgentOptions(
            allowed_tools=["Task", "Read", "Glob"],
            permission_mode="bypassPermissions",
            agents={
                "code-analyzer": AgentDefinition(
                    description="Analyzes Python code for quality and patterns",
                    prompt="Analyze code structure, patterns, and quality. Be concise.",
                    tools=["Read", "Glob"],
                ),
            },
        )
    ) as client:
        await client.query("Use the code-analyzer agent to analyze main.py.")

        async for message in client.receive_response():
            if isinstance(message, ResultMessage):
                print(f"\nDone. Cost: ${message.total_cost_usd:.4f}")
            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                    elif isinstance(block, ToolUseBlock) and block.name == "Task":
                        print(f"[subagent] {block.input.get('subagent_type')}")


async def main():
    await example_basic_query()
    await example_with_tools()
    await example_session_continuation()
    await example_custom_tools()
    await example_subagents()
    print("\nAll examples completed.")


if __name__ == "__main__":
    asyncio.run(main())
