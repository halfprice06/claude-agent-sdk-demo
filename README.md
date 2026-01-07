# Claude Agent SDK Demo

Demo showing how to build agents with the [Claude Agent SDK](https://platform.claude.com/docs/en/api/agent-sdk/overview).

## Quick Start

```bash
uv sync
cp .env.example .env  # Add your ANTHROPIC_API_KEY
uv run main.py
```

Get an API key from [console.anthropic.com](https://console.anthropic.com/).

## Examples

### 1. Basic Query
```python
async with ClaudeSDKClient(options=ClaudeAgentOptions(allowed_tools=[])) as client:
    await client.query("What is 2 + 2?")
    async for message in client.receive_response():
        print(message)
```

### 2. Built-in Tools
```python
options = ClaudeAgentOptions(allowed_tools=["Glob", "Read"], permission_mode="bypassPermissions")
```

### 3. Multi-turn Conversation
```python
async with ClaudeSDKClient(options=options) as client:
    await client.query("What files are here?")
    async for msg in client.receive_response(): ...

    await client.query("Tell me more about the first one")  # Retains context
    async for msg in client.receive_response(): ...
```

### 4. Custom Tools
```python
@tool(name="greet", description="Say hello", input_schema={"name": str})
async def greet(args):
    return {"content": [{"type": "text", "text": f"Hello {args['name']}!"}]}

server = create_sdk_mcp_server(name="my_tools", tools=[greet])
options = ClaudeAgentOptions(mcp_servers={"my_tools": server}, allowed_tools=["mcp__my_tools__greet"])
```

### 5. Subagents
```python
options = ClaudeAgentOptions(
    allowed_tools=["Task", "Read"],
    agents={
        "analyzer": AgentDefinition(
            description="Analyzes code",
            prompt="Analyze code quality. Be concise.",
            tools=["Read"]
        )
    }
)
```

## Resources

- [SDK Overview](https://platform.claude.com/docs/en/api/agent-sdk/overview)
- [Python Reference](https://platform.claude.com/docs/en/api/agent-sdk/python)
