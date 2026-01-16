# Kaizen Integration for CUGA Agent

This module integrates [Kaizen](https://github.com/AgentToolkit/kaizen) self-improving capabilities into CUGA Agent's lite mode, enabling the agent to learn from past executions and retrieve relevant guidelines for new tasks.

## Overview

The integration provides three main capabilities:

1. **Guideline Retrieval**: Before executing a task, CUGA retrieves relevant guidelines learned from previous successful executions
2. **Trajectory Capture**: During execution, CUGA captures the full trajectory (messages, tool calls, code executions)
3. **Automatic Learning**: After successful execution, trajectories are analyzed to generate new tips and best practices

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CUGA Lite Mode                         │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Task       │───▶│  Guideline   │───▶│  Execution   │ │
│  │   Input      │    │  Retrieval   │    │  with        │ │
│  └──────────────┘    └──────────────┘    │  Trajectory  │ │
│                                           │  Capture     │ │
│                                           └──────┬───────┘ │
│                                                  │         │
│                                           ┌──────▼───────┐ │
│                                           │  Trajectory  │ │
│                                           │  Save &      │ │
│                                           │  Tip Gen     │ │
│                                           └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   Kaizen Backend    │
                    │  (Filesystem/Milvus)│
                    │                     │
                    │  • Guidelines       │
                    │  • Trajectories     │
                    │  • Tips             │
                    └─────────────────────┘
```

## Components

### 1. KaizenAdapter (`kaizen_adapter.py`)

Main adapter class that interfaces with Kaizen's backend.

**Key Methods:**
- `get_guidelines(task, limit)`: Retrieve relevant guidelines for a task
- `save_trajectory(messages, task_id, generate_tips)`: Save execution trajectory
- `add_guideline(content, metadata)`: Manually add a guideline
- `get_stats()`: Get knowledge base statistics

**Example:**
```python
from cuga.backend.kaizen_integration import KaizenAdapter

adapter = KaizenAdapter(
    namespace_id="cuga_lite",
    provider="filesystem"
)

# Get guidelines
guidelines = adapter.get_guidelines("process customer data")

# Save trajectory
adapter.save_trajectory(
    messages=[...],
    task_id="task_123",
    generate_tips=True
)
```

### 2. TrajectoryCapture (`trajectory_capture.py`)

Captures execution trajectories in a structured format.

**Key Methods:**
- `add_user_message(content)`: Add user input
- `add_assistant_message(content)`: Add agent response
- `add_code_execution(code, output, success)`: Capture code execution
- `add_tool_call(tool_name, args, result)`: Capture tool usage
- `get_trajectory()`: Get captured messages

**Example:**
```python
from cuga.backend.kaizen_integration import TrajectoryCapture

trajectory = TrajectoryCapture()
trajectory.add_user_message("Calculate revenue")
trajectory.add_code_execution(
    code="revenue = sum(sales)",
    output="Total: $50000",
    success=True
)
```

### 3. CugaLiteKaizenIntegration (`cuga_lite_integration.py`)

Integration layer that hooks into CugaLite's execution flow.

**Key Methods:**
- `get_guidelines_for_task(task, state)`: Retrieve and format guidelines
- `start_trajectory_capture(task, state)`: Begin capturing
- `capture_step(step_type, content, metadata)`: Capture execution step
- `save_trajectory(final_answer, success, state)`: Save to Kaizen

**Example:**
```python
from cuga.backend.kaizen_integration.cuga_lite_integration import get_kaizen_integration

kaizen = get_kaizen_integration()

# Get guidelines
guidelines = kaizen.get_guidelines_for_task("analyze sales data")

# Start capture
kaizen.start_trajectory_capture("analyze sales data", state)

# Capture steps
kaizen.capture_code_execution(code, output, success=True)

# Save
kaizen.save_trajectory(final_answer="Analysis complete", success=True, state)
```

## Configuration

Add to `settings.toml`:

```toml
[kaizen]
enabled = true  # Enable Kaizen integration
kaizen_path = "~/Dev/oss/kaizen"  # Path to Kaizen installation
namespace_id = "cuga_lite"  # Namespace for guidelines
provider = "filesystem"  # Backend: 'filesystem' or 'milvus'
retrieve_guidelines = true  # Retrieve guidelines before execution
save_trajectories = true  # Save successful trajectories
generate_tips = true  # Generate tips from trajectories
guideline_limit = 5  # Max guidelines to retrieve
min_trajectory_length = 3  # Min messages to save
```

## Integration into CugaLite

To integrate Kaizen into CugaLite's execution flow, modify `cuga_lite_graph.py`:

### 1. Import the integration:

```python
from cuga.backend.kaizen_integration.cuga_lite_integration import get_kaizen_integration
```

### 2. Retrieve guidelines before execution:

```python
async def call_model(state: CugaLiteState, config: RunnableConfig):
    # Get Kaizen integration
    kaizen = get_kaizen_integration()
    
    # Retrieve guidelines
    guidelines = kaizen.get_guidelines_for_task(state.input, state)
    
    # Format and add to system prompt
    if guidelines:
        guideline_text = kaizen.format_guidelines_for_prompt(guidelines)
        system_prompt += guideline_text
    
    # Start trajectory capture
    kaizen.start_trajectory_capture(state.input, state)
    
    # ... rest of execution
```

### 3. Capture execution steps:

```python
# Capture code execution
kaizen.capture_code_execution(code, output, success=True)

# Capture tool calls
kaizen.capture_tool_call(tool_name, args, result)

# Capture thoughts/plans
kaizen.capture_step("thought", thought_content)
```

### 4. Save trajectory after completion:

```python
async def finalize(state: CugaLiteState):
    kaizen = get_kaizen_integration()
    
    # Save trajectory
    kaizen.save_trajectory(
        final_answer=state.final_answer,
        success=state.success,
        state=state
    )
    
    return state
```

## Usage Example

### Complete Integration Flow:

```python
from cuga.backend.kaizen_integration.cuga_lite_integration import get_kaizen_integration

# Initialize
kaizen = get_kaizen_integration()

# 1. Get guidelines before execution
task = "Calculate total revenue from sales data"
guidelines = kaizen.get_guidelines_for_task(task)

print("📚 Retrieved Guidelines:")
for i, guideline in enumerate(guidelines, 1):
    print(f"{i}. {guideline}")

# 2. Start trajectory capture
kaizen.start_trajectory_capture(task)

# 3. Capture execution steps
kaizen.capture_step("thought", "I need to load the sales data first")
kaizen.capture_code_execution(
    code="sales_data = load_sales()",
    output="Loaded 1000 records",
    success=True
)
kaizen.capture_code_execution(
    code="total = sum(sales_data['revenue'])",
    output="Total: $150000",
    success=True
)

# 4. Save trajectory
kaizen.save_trajectory(
    final_answer="Total revenue: $150,000",
    success=True
)

# 5. Check stats
stats = kaizen.get_stats()
print(f"Knowledge base: {stats['guidelines_count']} guidelines, {stats['trajectories_count']} trajectories")
```

## Backend Options

### Filesystem Backend (Default)
- **Pros**: Simple, no dependencies, easy debugging
- **Cons**: No semantic search, slower for large datasets
- **Best for**: Development, testing, small deployments

```toml
[kaizen]
provider = "filesystem"
```

### Milvus Backend
- **Pros**: Semantic search, fast, scalable
- **Cons**: Requires Milvus installation
- **Best for**: Production, large-scale deployments

```toml
[kaizen]
provider = "milvus"
```

## Testing

Test the integration:

```bash
# Navigate to CUGA directory
cd ~/Dev/oss/cuga-agent

# Run with Kaizen enabled
export KAIZEN_PROVIDER=filesystem
python -c "
from cuga.backend.kaizen_integration.cuga_lite_integration import get_kaizen_integration

kaizen = get_kaizen_integration()
print('Kaizen enabled:', kaizen.enabled)
print('Stats:', kaizen.get_stats())
"
```

## Troubleshooting

### Issue: Kaizen not initializing

**Solution**: Check that Kaizen path is correct:
```bash
ls ~/Dev/oss/kaizen/kaizen
```

### Issue: No guidelines retrieved

**Solution**: Add some initial guidelines:
```python
from cuga.backend.kaizen_integration import KaizenAdapter

adapter = KaizenAdapter()
adapter.add_guideline("Always validate input data before processing")
adapter.add_guideline("Use descriptive variable names")
```

### Issue: Trajectories not saving

**Solution**: Check minimum trajectory length:
```toml
[kaizen]
min_trajectory_length = 3  # Reduce if needed
```

## Benefits

1. **Continuous Improvement**: Agent learns from every successful execution
2. **Knowledge Retention**: Best practices are captured and reused
3. **Faster Execution**: Relevant guidelines help avoid common mistakes
4. **Consistency**: Similar tasks benefit from past learnings
5. **Transparency**: Full trajectory capture for debugging and analysis

## Future Enhancements

- [ ] Integration with CUGA's policy system
- [ ] Automatic guideline refinement based on success rates
- [ ] Multi-user guideline isolation
- [ ] Guideline versioning and rollback
- [ ] Integration with CUGA's memory system
- [ ] Real-time guideline suggestions during execution
- [ ] Guideline conflict detection and resolution

## License

This integration follows the same license as CUGA Agent (Apache 2.0).

## Contributing

Contributions are welcome! Please ensure:
1. Code follows CUGA's style guidelines
2. Tests are included for new features
3. Documentation is updated
4. Integration doesn't break existing functionality

## Support

For issues or questions:
- CUGA Issues: https://github.com/cuga-project/cuga-agent/issues
- Kaizen Issues: https://github.com/AgentToolkit/kaizen/issues