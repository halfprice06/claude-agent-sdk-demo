# Claude Agent SDK Demo

A simple, easy-to-understand demo showing how to build AI agents with the [Claude Agent SDK](https://platform.claude.com/docs/en/api/agent-sdk/overview).

## Features Demonstrated

1. **Basic Query** - Send prompts and stream responses
2. **Built-in Tools** - Use Read, Glob, Grep, Bash, etc.
3. **Multi-turn Conversations** - Maintain context across exchanges
4. **Custom Tools** - Create your own tools via MCP
5. **Subagents** - Delegate to specialized agents

## Quick Start

### 1. Install dependencies

```bash
uv sync
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

Get your API key from [console.anthropic.com](https://console.anthropic.com/).

### 3. Run the demo

```bash
uv run main.py
```

## Project Structure

```
demo/
├── main.py          # All examples with detailed comments
├── pyproject.toml   # Project config & dependencies
├── uv.lock          # Locked dependencies
├── .env.example     # API key template
└── README.md        # This file
```

## Examples Overview

### Example 1: Basic Query
```python
async for message in query(prompt="Hello!"):
    print(message)
```

### Example 2: Using Tools
```python
async for message in query(
    prompt="List Python files",
    options=ClaudeAgentOptions(allowed_tools=["Glob"])
):
    print(message)
```

### Example 3: Multi-turn Conversation
```python
async with ClaudeSDKClient() as client:
    await client.query("What files are here?")
    # ... process response ...
    await client.query("Tell me more about the first one")  # Remembers context!
```

### Example 4: Custom Tools
```python
@tool("greet", "Say hello", {"name": str})
async def greet(args):
    return {"content": [{"type": "text", "text": f"Hello {args['name']}!"}]}
```

### Example 5: Subagents
```python
options = ClaudeAgentOptions(
    agents={
        "analyzer": AgentDefinition(
            description="Analyzes code",
            prompt="You analyze code quality",
            tools=["Read"]
        )
    }
)
```

## Resources

- [Agent SDK Overview](https://platform.claude.com/docs/en/api/agent-sdk/overview)
- [Python SDK Reference](https://platform.claude.com/docs/en/api/agent-sdk/python)
- [Example Agents](https://github.com/anthropics/claude-agent-sdk-demos)
