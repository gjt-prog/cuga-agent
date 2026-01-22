# Kaizen MCP Integration Example

This example demonstrates how to use Kaizen's self-improving capabilities with CUGA Agent through the Model Context Protocol (MCP).

## Overview

Instead of tightly coupling Kaizen into CUGA's codebase, this approach uses MCP to provide Kaizen's functionality as tools that CUGA can call. This creates a clean separation of concerns and makes Kaizen an optional, pluggable component.

## Prerequisites

1. **CUGA Agent** installed
2. **Kaizen** installed (clone from https://github.com/AgentToolkit/kaizen)
3. **Python 3.10+**

## Setup

### 1. Install Kaizen

```bash
# Clone Kaizen repository
cd ~/Dev/oss
git clone https://github.com/AgentToolkit/kaizen.git
cd kaizen

# Install Kaizen
pip install -e .
```

### 2. Configure MCP Server

Copy the example configuration:

```bash
# From CUGA root directory
cp docs/examples/kaizen_mcp/mcp_servers.yaml ./mcp_servers.yaml
```

Edit `mcp_servers.yaml` to match your Kaizen installation path:

```yaml
kaizen:
  command: "uv"
  args:
    - "run"
    - "python"
    - "-m"
    - "cuga.backend.server.mcp_servers.kaizen_mcp"
  env:
    KAIZEN_PATH: "~/Dev/oss/kaizen"  # Adjust this path
    KAIZEN_PROVIDER: "filesystem"
```

### 3. Test the MCP Server

Run the server standalone to verify it works:

```bash
export KAIZEN_PATH="~/Dev/oss/kaizen"
export KAIZEN_PROVIDER="filesystem"

uv run python -m cuga.backend.server.mcp_servers.kaizen_mcp
```

You should see: `✅ Kaizen MCP server initialized`

## Usage

### Basic Example

```python
from cuga.sdk import CugaAgent

# Initialize CUGA with MCP servers configuration
agent = CugaAgent(
    mcp_servers_config="mcp_servers.yaml"
)

# The agent now has access to Kaizen tools:
# - kaizen_get_guidelines
# - kaizen_save_trajectory
# - kaizen_add_guideline
# - kaizen_get_stats

# Run a task - Kaizen tools are automatically available
result = await agent.run(
    "Analyze the sales data and generate a report"
)

# The agent can use Kaizen tools during execution:
# 1. Retrieve relevant guidelines before starting
# 2. Save the execution trajectory after completion
# 3. Generate tips from successful executions
```

### Manual Tool Usage

```python
from langchain_mcp_adapters import MCPToolkit

# Initialize MCP toolkit
toolkit = MCPToolkit(config_path="mcp_servers.yaml")

# Get Kaizen tools
tools = toolkit.get_tools()
kaizen_tools = [t for t in tools if t.name.startswith('kaizen_')]

# Use tools directly
for tool in kaizen_tools:
    print(f"Available: {tool.name} - {tool.description}")

# Get guidelines
guidelines_tool = next(t for t in kaizen_tools if t.name == 'kaizen_get_guidelines')
guidelines = await guidelines_tool.ainvoke({
    "task": "Process customer data",
    "limit": 5
})

print("Retrieved guidelines:")
for guideline in guidelines:
    print(f"  - {guideline}")
```

### Adding Initial Guidelines

```python
# Add some initial guidelines to bootstrap the knowledge base
add_guideline_tool = next(t for t in kaizen_tools if t.name == 'kaizen_add_guideline')

guidelines = [
    "Always validate input data before processing",
    "Use descriptive variable names for clarity",
    "Handle errors gracefully with try-except blocks",
    "Log important steps for debugging",
    "Test edge cases thoroughly"
]

for guideline in guidelines:
    result = await add_guideline_tool.ainvoke({
        "content": guideline,
        "namespace_id": "cuga_lite"
    })
    print(f"Added: {guideline}")
```

### Checking Statistics

```python
# Get knowledge base statistics
stats_tool = next(t for t in kaizen_tools if t.name == 'kaizen_get_stats')
stats = await stats_tool.ainvoke({"namespace_id": "cuga_lite"})

print(f"Knowledge Base Stats:")
print(f"  Guidelines: {stats['guidelines_count']}")
print(f"  Trajectories: {stats['trajectories_count']}")
print(f"  Total Entities: {stats['total_entities']}")
```

## How It Works

### 1. Guideline Retrieval

Before executing a task, CUGA can retrieve relevant guidelines:

```
User: "Analyze sales data"
  ↓
CUGA calls: kaizen_get_guidelines(task="Analyze sales data")
  ↓
Kaizen MCP Server searches knowledge base
  ↓
Returns: ["Use pandas for data analysis", "Validate data types", ...]
  ↓
CUGA includes guidelines in execution context
```

### 2. Trajectory Capture

During execution, CUGA captures the trajectory:

```
Execution starts
  ↓
User message: "Analyze sales data"
  ↓
Assistant: "I'll load and analyze the data"
  ↓
Code execution: "df = pd.read_csv('sales.csv')"
  ↓
Output: "Loaded 1000 rows"
  ↓
... more steps ...
  ↓
Final answer: "Total revenue: $50,000"
```

### 3. Trajectory Saving

After successful execution, save the trajectory:

```
CUGA calls: kaizen_save_trajectory(
    messages=[...],
    task_id="sales_analysis_001",
    generate_tips=True
)
  ↓
Kaizen MCP Server saves trajectory
  ↓
Generates tips from successful execution
  ↓
Stores tips as new guidelines
  ↓
Future similar tasks benefit from learned knowledge
```

## Benefits

1. **Loose Coupling**: Kaizen is optional and can be disabled
2. **Clean Architecture**: MCP provides standard interface
3. **Easy Testing**: Can mock MCP tools for testing
4. **Flexibility**: Easy to swap or upgrade Kaizen
5. **Process Isolation**: Kaizen runs in separate process
6. **No Code Changes**: CUGA code doesn't need Kaizen imports




## Resources

- [Kaizen GitHub](https://github.com/AgentToolkit/kaizen)
- [MCP Protocol](https://modelcontextprotocol.io)
- [CUGA Documentation](https://cuga.dev)
