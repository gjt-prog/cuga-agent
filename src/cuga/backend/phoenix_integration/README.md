# Phoenix (Arize) Observability Integration for CUGA

This module provides comprehensive observability for CUGA agent executions using [Phoenix (Arize-Phoenix)](https://github.com/Arize-ai/phoenix), an open-source LLM observability platform.

## 🎯 Features

- **Automatic LLM Tracing**: Captures all LangChain LLM calls automatically
- **Tool Execution Monitoring**: Tracks tool calls, inputs, outputs, and performance
- **Agent Workflow Visualization**: Visualizes agent decision-making and execution flow
- **Performance Metrics**: Monitors latency, token usage, and resource consumption
- **Error Tracking**: Captures and categorizes errors for debugging
- **Real-time Dashboard**: Phoenix UI for live monitoring and analysis

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CUGA Agent                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  LangChain   │  │    Tools     │  │   Workflow   │     │
│  │   LLM Calls  │  │  Executions  │  │    Steps     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                            ▼                                 │
│         ┌──────────────────────────────────┐                │
│         │  CugaPhoenixIntegration          │                │
│         │  - start_agent_trace()           │                │
│         │  - log_tool_execution()          │                │
│         │  - log_agent_step()              │                │
│         │  - log_llm_call()                │                │
│         │  - log_error()                   │                │
│         └──────────────┬───────────────────┘                │
│                        │                                     │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │      PhoenixTracer            │
         │  - Auto-instrumentation       │
         │  - Trace management           │
         │  - Metrics collection         │
         └──────────────┬────────────────┘
                        │
                        ▼
         ┌───────────────────────────────┐
         │   Phoenix Server/Collector    │
         │   - Data storage              │
         │   - Analytics engine          │
         │   - Web UI (port 6006)        │
         └───────────────────────────────┘
```

## 🚀 Quick Start

### 1. Installation

Install Phoenix as an optional dependency:

```bash
# Using uv
cd /Users/gsthomas/Dev/oss/cuga-agent
source .venv/bin/activate
uv pip install -e ".[phoenix]"

# Or using pip
pip install "cuga[phoenix]"
```

This installs:
- `arize-phoenix>=5.0.0` - Phoenix observability platform
- `openinference-instrumentation-langchain>=0.1.0` - LangChain auto-instrumentation

### 2. Configuration

Enable Phoenix in `settings.toml`:

```toml
[phoenix]
enabled = true  # Enable Phoenix observability
project_name = "cuga-agent"  # Phoenix project name
phoenix_host = "http://localhost"  # Phoenix server host
phoenix_port = 6006  # Phoenix server port
auto_instrument_langchain = true  # Auto-instrument LangChain
launch_phoenix = false  # Launch Phoenix server locally
```

### 3. Start Phoenix Server

**Option A: Launch automatically (recommended for development)**

Set `launch_phoenix = true` in settings.toml. Phoenix will start automatically when CUGA initializes.

**Option B: Launch manually**

```bash
# Start Phoenix server
python -m phoenix.server.main serve

# Or with custom port
python -m phoenix.server.main serve --port 6006
```

**Option C: Use Docker**

```bash
docker run -p 6006:6006 -p 4317:4317 arizephoenix/phoenix:latest
```

### 4. Run CUGA with Phoenix

```python
from cuga import CugaAgent

# Phoenix will automatically trace all operations
agent = CugaAgent()
result = agent.run("Your task here")

# View traces at http://localhost:6006
```

## 📊 Using the Phoenix UI

Once Phoenix is running, access the UI at `http://localhost:6006`:

### Dashboard Features

1. **Traces View**
   - See all agent executions in real-time
   - Drill down into individual traces
   - View LLM calls, tool executions, and timing

2. **Projects**
   - Organize traces by project (default: "cuga-agent")
   - Compare performance across projects

3. **Analytics**
   - Token usage statistics
   - Latency distributions
   - Error rates and types
   - Tool usage patterns

4. **Search & Filter**
   - Filter by time range
   - Search by task, tool, or error
   - Filter by success/failure

## 🔧 Advanced Usage

### Manual Instrumentation

For custom logging beyond auto-instrumentation:

```python
from cuga.backend.phoenix_integration import get_cuga_phoenix_integration

# Get integration instance
phoenix = get_cuga_phoenix_integration()

# Start agent trace
trace_context = phoenix.start_agent_trace(
    task="Process customer data",
    state=agent_state
)

# Log tool execution
phoenix.log_tool_execution(
    tool_name="get_customer_data",
    tool_input={"customer_id": "12345"},
    tool_output={"name": "John Doe", "email": "john@example.com"},
    success=True,
    execution_time=0.5
)

# Log agent step
phoenix.log_agent_step(
    step_name="data_validation",
    step_type="validation",
    input_data=raw_data,
    output_data=validated_data,
    state=agent_state
)

# Log LLM call (if not auto-instrumented)
phoenix.log_llm_call(
    model="gpt-4",
    prompt="Analyze this data...",
    response="The data shows...",
    tokens_used=150,
    latency=1.2
)

# Log errors
phoenix.log_error(
    error_type="ValidationError",
    error_message="Invalid customer ID format",
    stack_trace=traceback.format_exc(),
    context={"customer_id": "invalid-id"}
)
```

### Integration with CUGA Lite Mode

Phoenix automatically traces CugaLite executions:

```python
# In cuga_lite_graph.py
from cuga.backend.phoenix_integration import get_cuga_phoenix_integration

async def call_model(state: CugaLiteState, config: RunnableConfig):
    phoenix = get_cuga_phoenix_integration()
    
    # Start trace
    phoenix.start_agent_trace(state.input, state)
    
    # Execute model (auto-traced by LangChain instrumentation)
    response = await model.ainvoke(messages)
    
    # Log custom step
    phoenix.log_agent_step(
        step_name="model_call",
        step_type="llm_inference",
        input_data=messages,
        output_data=response,
        state=state
    )
    
    return state
```

### Custom Collector Endpoint

For production deployments with a separate Phoenix collector:

```toml
[phoenix]
enabled = true
phoenix_collector_endpoint = "https://phoenix.your-company.com:4317"
```

## 📈 Metrics & Analytics

Phoenix automatically collects:

### LLM Metrics
- **Token Usage**: Input/output tokens per call
- **Latency**: Response time distribution
- **Cost**: Estimated API costs (if configured)
- **Model Performance**: Success rates, error rates

### Tool Metrics
- **Execution Time**: Tool call latency
- **Success Rate**: Percentage of successful executions
- **Usage Patterns**: Most/least used tools
- **Error Analysis**: Common failure modes

### Agent Metrics
- **Task Completion Time**: End-to-end execution time
- **Step Count**: Number of steps per task
- **Decision Quality**: Success/failure rates
- **Resource Usage**: Memory, CPU, API calls

## 🐛 Debugging with Phoenix

### Finding Errors

1. **Filter by Status**: Use the UI to filter failed traces
2. **Error Details**: Click on failed traces to see error messages and stack traces
3. **Context**: View the full execution context leading to the error
4. **Patterns**: Identify common error patterns across traces

### Performance Optimization

1. **Identify Bottlenecks**: Find slow LLM calls or tool executions
2. **Token Optimization**: Analyze token usage to reduce costs
3. **Caching Opportunities**: Identify repeated calls that could be cached
4. **Parallel Execution**: Find sequential operations that could run in parallel

## 🔒 Security & Privacy

### Data Handling

- **Local by Default**: Phoenix runs locally, data stays on your machine
- **No External Calls**: Unless using a remote collector endpoint
- **Sensitive Data**: Consider filtering sensitive information before logging

### Production Considerations

```toml
[phoenix]
enabled = true
# Use environment-specific collector
phoenix_collector_endpoint = "${PHOENIX_COLLECTOR_ENDPOINT}"
# Disable auto-launch in production
launch_phoenix = false
```

## 🧪 Testing

Test the Phoenix integration:

```bash
cd /Users/gsthomas/Dev/oss/cuga-agent
source .venv/bin/activate
python test_phoenix_integration.py
```

## 📚 API Reference

### PhoenixTracer

Main tracer class for Phoenix integration.

```python
class PhoenixTracer:
    def __init__(
        self,
        project_name: str = "cuga-agent",
        phoenix_host: str = "http://localhost",
        phoenix_port: int = 6006,
        enabled: bool = True,
        auto_instrument_langchain: bool = True,
        launch_phoenix: bool = False,
        phoenix_collector_endpoint: Optional[str] = None
    )
    
    def start_trace(self, trace_name: str, metadata: Optional[Dict] = None)
    def log_llm_call(self, model: str, prompt: str, response: str, metadata: Optional[Dict] = None)
    def log_tool_execution(self, tool_name: str, tool_input: Dict, tool_output: Any, success: bool = True, error: Optional[str] = None, metadata: Optional[Dict] = None)
    def log_agent_step(self, step_name: str, step_type: str, input_data: Any, output_data: Any, metadata: Optional[Dict] = None)
    def log_error(self, error_type: str, error_message: str, stack_trace: Optional[str] = None, metadata: Optional[Dict] = None)
    def get_stats(self) -> Dict[str, Any]
    def shutdown(self)
```

### CugaPhoenixIntegration

CUGA-specific integration layer.

```python
class CugaPhoenixIntegration:
    def start_agent_trace(self, task: str, state: Optional[AgentState] = None)
    def log_tool_execution(self, tool_name: str, tool_input: Dict, tool_output: Any, success: bool = True, error: Optional[str] = None, execution_time: Optional[float] = None)
    def log_agent_step(self, step_name: str, step_type: str, input_data: Any, output_data: Any, state: Optional[AgentState] = None)
    def log_llm_call(self, model: str, prompt: str, response: str, tokens_used: Optional[int] = None, latency: Optional[float] = None)
    def log_error(self, error_type: str, error_message: str, stack_trace: Optional[str] = None, context: Optional[Dict] = None)
    def get_stats(self) -> Dict[str, Any]
    def shutdown(self)
```

## 🔗 Integration with Other CUGA Features

### With Kaizen Self-Improvement

Phoenix traces can inform Kaizen's learning:

```python
# Phoenix captures execution details
phoenix.start_agent_trace(task, state)

# Kaizen learns from successful patterns
kaizen.save_trajectory(messages, task_id, generate_tips=True)

# Analyze Phoenix traces to identify patterns for Kaizen guidelines
```

### With Activity Tracker

Phoenix complements CUGA's activity tracker:

- **Activity Tracker**: Task-level logging, trajectory storage
- **Phoenix**: Real-time observability, performance metrics, debugging

Both can run simultaneously for comprehensive monitoring.

## 🆘 Troubleshooting

### Phoenix Not Starting

```bash
# Check if Phoenix is installed
python -c "import phoenix; print(phoenix.__version__)"

# Install if missing
uv pip install -e ".[phoenix]"
```

### No Traces Appearing

1. **Check Configuration**: Ensure `enabled = true` in settings.toml
2. **Verify Server**: Confirm Phoenix server is running at configured endpoint
3. **Check Logs**: Look for Phoenix initialization messages in CUGA logs
4. **Network**: Ensure no firewall blocking port 6006

### Auto-Instrumentation Not Working

```python
# Verify LangChain instrumentation
from cuga.backend.phoenix_integration import get_phoenix_tracer

tracer = get_phoenix_tracer()
stats = tracer.get_stats()
print(f"Auto-instrumentation: {stats['auto_instrument_langchain']}")
```

## 📖 Additional Resources

- [Phoenix Documentation](https://docs.arize.com/phoenix)
- [Phoenix GitHub](https://github.com/Arize-ai/phoenix)
- [OpenInference Specification](https://github.com/Arize-ai/openinference)
- [LangChain Integration Guide](https://docs.arize.com/phoenix/tracing/integrations-tracing/langchain)

## 🤝 Contributing

To improve Phoenix integration:

1. Add new instrumentation points in `phoenix_tracer.py`
2. Extend CUGA-specific hooks in `cuga_phoenix_integration.py`
3. Update tests in `test_phoenix_integration.py`
4. Document changes in this README

## 📝 License

This integration follows CUGA's Apache-2.0 license.