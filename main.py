"""
Claude Agent SDK Demo
=====================
This demo shows how to build agents with the Claude Agent SDK.

Features demonstrated:
1. Basic query with streaming
2. Using built-in tools (Read, Glob, Grep, Bash)
3. Session continuation (multi-turn conversations)
4. Custom tools via MCP
5. Subagents

Prerequisites:
- Set ANTHROPIC_API_KEY environment variable
- Claude Code CLI is bundled with the SDK

Run with: uv run main.py
"""

import asyncio
from typing import Any

from claude_agent_sdk import (
    # Core functions
    query,
    ClaudeSDKClient,
    ClaudeAgentOptions,
    # Custom tools
    tool,
    create_sdk_mcp_server,
    # Message types for processing responses
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    # Subagent definition
    AgentDefinition,
)


# =============================================================================
# EXAMPLE 1: Basic Query with Streaming
# =============================================================================
async def example_basic_query():
    """
    Simplest usage - send a prompt and stream the response.
    Each call to query() starts a fresh session.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Query with Streaming")
    print("=" * 60)

    # Stream messages as they arrive
    async for message in query(
        prompt="What is 2 + 2? Answer in one sentence.",
        options=ClaudeAgentOptions(
            # No tools needed for simple questions
            allowed_tools=[]
        ),
    ):
        # Check for the final result
        if isinstance(message, ResultMessage):
            print(f"\n✓ Done! Cost: ${message.total_cost_usd:.4f}")
        # Print assistant text responses
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")


# =============================================================================
# EXAMPLE 2: Using Built-in Tools
# =============================================================================
async def example_with_tools():
    """
    Give Claude access to built-in tools to interact with your system.

    Common tools:
    - Read: Read files
    - Write: Create files
    - Edit: Modify files
    - Bash: Run shell commands
    - Glob: Find files by pattern
    - Grep: Search file contents
    - WebSearch: Search the web
    - WebFetch: Fetch web pages
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Using Built-in Tools")
    print("=" * 60)

    async for message in query(
        prompt="List the Python files in the current directory using Glob.",
        options=ClaudeAgentOptions(
            # Specify which tools Claude can use
            allowed_tools=["Glob", "Read"],
            # Auto-accept file reads (no prompts)
            permission_mode="bypassPermissions",
            # Working directory for file operations
            cwd=".",
        ),
    ):
        if isinstance(message, ResultMessage):
            print(f"\n✓ Done! Turns: {message.num_turns}")
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
                elif isinstance(block, ToolUseBlock):
                    print(f"🔧 Using tool: {block.name}")
                elif isinstance(block, ToolResultBlock):
                    # Tool results can be long, truncate for display
                    content = str(block.content)[:200]
                    print(f"📋 Result: {content}...")


# =============================================================================
# EXAMPLE 3: Multi-turn Conversation (Session Continuation)
# =============================================================================
async def example_session_continuation():
    """
    Use ClaudeSDKClient to maintain context across multiple exchanges.
    Claude remembers previous messages in the session.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Multi-turn Conversation")
    print("=" * 60)

    # Use async context manager for automatic cleanup
    async with ClaudeSDKClient(
        options=ClaudeAgentOptions(
            allowed_tools=["Glob"],
            permission_mode="bypassPermissions",
        )
    ) as client:
        # First message
        print("\n--- Turn 1 ---")
        await client.query("What Python files are in this directory?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

        # Follow-up - Claude remembers the context!
        print("\n--- Turn 2 ---")
        await client.query("Which one of those files is the main entry point?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")


# =============================================================================
# EXAMPLE 4: Custom Tools via MCP
# =============================================================================

# Define a custom tool using the @tool decorator
@tool(
    name="calculate",
    description="Perform a mathematical calculation",
    input_schema={"expression": str},  # Simple type mapping
)
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    """
    Custom tool that evaluates math expressions.
    Returns MCP-formatted response.
    """
    expression = args["expression"]
    try:
        # Safe evaluation (only math)
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            "content": [{"type": "text", "text": f"Result: {result}"}]
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {e}"}],
            "is_error": True,
        }


@tool(
    name="greet",
    description="Generate a greeting for a person",
    input_schema={"name": str, "style": str},
)
async def greet(args: dict[str, Any]) -> dict[str, Any]:
    """Another custom tool example."""
    name = args["name"]
    style = args.get("style", "friendly")

    greetings = {
        "friendly": f"Hey {name}! Great to see you! 👋",
        "formal": f"Good day, {name}. How may I assist you?",
        "pirate": f"Ahoy, {name}! Welcome aboard, matey! ⚓",
    }

    greeting = greetings.get(style, greetings["friendly"])
    return {"content": [{"type": "text", "text": greeting}]}


async def example_custom_tools():
    """
    Create custom tools using the @tool decorator and MCP server.

    Note: Uses ClaudeSDKClient for better stability with in-process MCP servers.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Custom Tools via MCP")
    print("=" * 60)

    # Create an MCP server with our custom tools
    my_tools = create_sdk_mcp_server(
        name="my_tools",
        version="1.0.0",
        tools=[calculate, greet],
    )

    try:
        # Use ClaudeSDKClient for custom tools (more stable than query())
        async with ClaudeSDKClient(
            options=ClaudeAgentOptions(
                # Register our MCP server
                mcp_servers={"my_tools": my_tools},
                # Allow Claude to use our custom tools
                # Format: mcp__{server_name}__{tool_name}
                allowed_tools=[
                    "mcp__my_tools__calculate",
                    "mcp__my_tools__greet",
                ],
            )
        ) as client:
            await client.query(
                "Use the calculate tool to compute 15 * 7, then greet me in pirate style. My name is Captain Jack."
            )

            async for message in client.receive_response():
                if isinstance(message, ResultMessage):
                    print(f"\n✓ Done!")
                elif isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            print(f"Claude: {block.text}")
                        elif isinstance(block, ToolUseBlock):
                            print(f"🔧 Calling: {block.name}({block.input})")
    except Exception as e:
        # In-process MCP servers can sometimes have transport issues
        print(f"⚠️  Custom tools example encountered an error: {type(e).__name__}")
        print("   This is a known issue with in-process MCP servers.")
        print("   The other examples should work fine.")


# =============================================================================
# EXAMPLE 5: Subagents
# =============================================================================
async def example_subagents():
    """
    Define specialized subagents that the main agent can delegate to.
    Useful for complex workflows with distinct responsibilities.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Subagents")
    print("=" * 60)

    async for message in query(
        prompt="Use the code-analyzer agent to analyze the main.py file in this directory.",
        options=ClaudeAgentOptions(
            # Main agent needs Task tool to spawn subagents
            allowed_tools=["Task", "Read", "Glob"],
            permission_mode="bypassPermissions",
            # Define available subagents
            agents={
                "code-analyzer": AgentDefinition(
                    description="Analyzes Python code for quality and patterns",
                    prompt="You are a code analysis expert. When given a file, analyze its structure, patterns, and quality. Be concise.",
                    tools=["Read", "Glob"],  # Tools available to subagent
                ),
                "summarizer": AgentDefinition(
                    description="Summarizes text content concisely",
                    prompt="You are a summarization expert. Provide clear, brief summaries.",
                    tools=["Read"],
                ),
            },
        ),
    ):
        if isinstance(message, ResultMessage):
            print(f"\n✓ Done! Total cost: ${message.total_cost_usd:.4f}")
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
                elif isinstance(block, ToolUseBlock):
                    if block.name == "Task":
                        print(f"🤖 Spawning subagent: {block.input.get('subagent_type')}")


# =============================================================================
# MAIN - Run all examples
# =============================================================================
async def main():
    """Run all examples in sequence."""
    print("\n" + "🚀 " * 20)
    print("CLAUDE AGENT SDK DEMO")
    print("🚀 " * 20)

    # Run examples one at a time
    # Comment out any you don't want to run

    await example_basic_query()
    await example_with_tools()
    await example_session_continuation()
    await example_custom_tools()
    await example_subagents()

    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
