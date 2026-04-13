# LangChain 1.0 Alpha - Complete Usage Guide

## Table of Contents
1. [Installation](#installation)
2. [Quick Start: Basic Model Calling](#quick-start-basic-model-calling)
3. [Working with Tools](#working-with-tools)
4. [Building Agents](#building-agents)
5. [Agent Termination Control](#agent-termination-control)
6. [Conversation State & Memory](#conversation-state--memory)
7. [Middleware System](#middleware-system)
8. [Structured Output](#structured-output)
9. [Understanding LangGraph](#understanding-langgraph)
10. [Production Patterns](#production-patterns)
11. [Common Pitfalls](#common-pitfalls)

---

## Installation

```bash
# Install LangChain 1.0 alpha
pip install langchain==1.0.0a15

# Install provider packages you need
pip install langchain-anthropic  # For Claude
pip install langchain-openai     # For GPT-4
pip install langchain-google-genai  # For Gemini

# Core dependency (should auto-install)
pip install langchain-core
```

**Pin your versions** in `requirements.txt`:
```
langchain==1.0.0a15
langchain-core==1.0.0rc1
langchain-anthropic==1.0.0a5
langchain-openai==1.0.0a4
```

---

## Quick Start: Basic Model Calling

### Simple Text Generation

```python
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

# Initialize any model with consistent API
model = init_chat_model("anthropic:claude-3-sonnet-20240229")

# Make a simple call
response = model.invoke([HumanMessage(content="What is AI?")])
print(response.content)
```

### Switching Providers (Same API)

```python
# Anthropic
model = init_chat_model("anthropic:claude-3-sonnet-20240229")

# OpenAI
model = init_chat_model("openai:gpt-4")

# Google
model = init_chat_model("google:gemini-pro")

# Always the same invoke() method
response = model.invoke([HumanMessage(content="Hello")])
```

### With System Prompt

```python
from langchain_core.messages import SystemMessage, HumanMessage

model = init_chat_model("anthropic:claude-3-sonnet-20240229")

messages = [
    SystemMessage(content="You are a helpful Python tutor"),
    HumanMessage(content="How do I use list comprehensions?")
]

response = model.invoke(messages)
print(response.content)
```

### Streaming Responses

```python
model = init_chat_model("anthropic:claude-3-sonnet-20240229")

for chunk in model.stream([HumanMessage(content="Write a poem")]):
    print(chunk.content, end="", flush=True)
print()  # newline
```

### Simple Conversation

```python
# Maintain message history manually
messages = []

def chat(user_input: str):
    messages.append(HumanMessage(content=user_input))
    response = model.invoke(messages)
    messages.append(response)
    return response.content

# Use it
print(chat("My name is Alice"))
print(chat("What's my name?"))  # Remembers Alice
```

---

## Working with Tools

### Basic Tool Definition

```python
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

def get_weather(location: str) -> str:
    """Get the current weather for a location.

    Args:
        location: The city name to get weather for
    """
    # In reality, call a weather API
    return f"Sunny and 72°F in {location}"

# Bind tools to model
model = init_chat_model("anthropic:claude-3-sonnet-20240229")
model_with_tools = model.bind_tools([get_weather])

# Model can now call the tool
response = model_with_tools.invoke([
    HumanMessage(content="What's the weather in San Francisco?")
])

# Check if model wants to use tool
if response.tool_calls:
    print(f"Model wants to call: {response.tool_calls}")
    # You'd execute the tool and continue the conversation
else:
    print(response.content)
```

### Using @tool Decorator

```python
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.

    Args:
        expression: A valid Python math expression like "2+2" or "10*5"
    """
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

@tool
def search_web(query: str) -> str:
    """Search the web for information.

    Args:
        query: The search query
    """
    # In reality, call a search API
    return f"Search results for: {query}"

# Use with model
model = init_chat_model("anthropic:claude-3-sonnet-20240229")
model_with_tools = model.bind_tools([calculator, search_web])
```

---

## Building Agents

### Your First Agent

```python
from langchain.agents import create_agent

def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Sunny in {location}"

# Create agent - handles tool loop automatically
agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[get_weather],
    system_prompt="You are a helpful weather assistant",
)

# Use agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "What's the weather in SF?"}]
})

print(result["messages"][-1].content)
```

### Multi-Tool Agent

```python
from langchain.agents import create_agent
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """Calculate a math expression."""
    return str(eval(expression))

@tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"Sunny in {location}"

@tool
def search_web(query: str) -> str:
    """Search the web."""
    return f"Search results for: {query}"

agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[calculator, get_weather, search_web],
    system_prompt="You are a helpful assistant with access to tools",
)

# Agent automatically:
# 1. Calls model
# 2. Detects tool calls
# 3. Executes tools (in parallel if multiple)
# 4. Feeds results back to model
# 5. Repeats until model returns final answer
# 6. Returns complete conversation

result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "What's the weather in SF and what's 25 * 4?"
    }]
})
```

### Agent with Streaming

```python
agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[calculator, search_web],
)

# Stream agent execution
for event in agent.stream(
    {"messages": [{"role": "user", "content": "Research AI and calculate market size"}]},
    stream_mode="values"  # Get full state updates
):
    # Print last message in conversation
    print(f"\n{'='*50}")
    print(event["messages"][-1])
```

---

## Agent Termination Control

### 1. Natural Termination (Default)

The agent stops when the model returns text **without** tool calls:

```python
agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[calculator],
)

# Agent stops when model says "The answer is 4" (no tool calls)
result = agent.invoke({
    "messages": [{"role": "user", "content": "What is 2+2?"}]
})
```

### 2. System Prompt Guidance

Tell the model explicitly when to stop:

```python
agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[search_web, calculator],
    system_prompt="""You are a research assistant.

When answering questions:
1. Use search_web to find information
2. Use calculator for math
3. After gathering information, provide a COMPLETE answer
4. Do NOT ask follow-up questions - answer with what you have
5. STOP after providing your answer

Remember: Your job is to answer the question, then STOP."""
)
```

### 3. Structured Response (Forces Stop)

```python
from pydantic import BaseModel

class WeatherReport(BaseModel):
    location: str
    temperature: int
    conditions: str
    recommendation: str

agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[get_weather],
    response_format=WeatherReport,
)

# Agent MUST stop when it returns a valid WeatherReport
result = agent.invoke({
    "messages": [{"role": "user", "content": "Weather in SF?"}]
})

# Access structured response
weather = result["structured_response"]
print(f"Temperature: {weather.temperature}°F")
```

### 4. Tool with return_direct=True

```python
from langchain_core.tools import tool

@tool(return_direct=True)
def final_answer(answer: str) -> str:
    """Provide the final answer to the user. Call when done."""
    return answer

agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[search_web, calculator, final_answer],
    system_prompt="Research the question, then call final_answer with your response"
)

# Agent will:
# 1. Use search_web/calculator as needed
# 2. Call final_answer("The answer is...")
# 3. STOP IMMEDIATELY (return_direct=True)
```

### 5. Recursion Limit (Safety)

```python
from langgraph.errors import GraphRecursionError

agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[search_web],
)

try:
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Research topic"}]},
        {"recursion_limit": 10}  # Max 10 iterations
    )
except GraphRecursionError:
    print("Agent hit recursion limit - possibly stuck in loop")
```

---

## Conversation State & Memory

### Using Checkpointer for Persistence

```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

# Create agent with checkpointer
agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[calculator],
    checkpointer=MemorySaver(),  # Stores conversation in memory
)

# Each conversation needs a unique thread_id
config = {"configurable": {"thread_id": "user-123"}}

# First message
agent.invoke(
    {"messages": [{"role": "user", "content": "My name is Alice"}]},
    config=config
)

# Later conversation (same thread_id)
result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's my name?"}]},
    config=config
)
# Outputs: "Your name is Alice"
```

### PostgreSQL Persistence

```python
from langgraph.checkpoint.postgres import PostgresSaver

# Production-grade persistence
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost/db"
)

agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[...],
    checkpointer=checkpointer,
)

# Conversations survive server restarts
# Multiple users isolated by thread_id
```

### Multi-User Conversations

```python
agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[...],
    checkpointer=checkpointer,
)

# User 1's conversation
user1_config = {"configurable": {"thread_id": "user-1"}}
agent.invoke({"messages": [{"role": "user", "content": "Hello"}]}, user1_config)

# User 2's conversation (completely separate)
user2_config = {"configurable": {"thread_id": "user-2"}}
agent.invoke({"messages": [{"role": "user", "content": "Hi"}]}, user2_config)

# Each user has isolated conversation history
```

---

## Middleware System

### Basic Middleware

```python
from langchain.agents import create_agent, AgentMiddleware

class LoggingMiddleware(AgentMiddleware):
    """Log all model calls."""

    def before_model(self, state, runtime):
        """Called before each model invocation."""
        print(f"About to call model with {len(state['messages'])} messages")
        return {}

    def after_model(self, state, runtime):
        """Called after each model invocation."""
        last_msg = state["messages"][-1]
        print(f"Model responded: {last_msg.content[:50]}...")
        return {}

agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[calculator],
    middleware=[LoggingMiddleware()],
)
```

### Model Request Wrapper (Auth, Retry, Rate Limiting)

```python
import time

class RateLimitMiddleware(AgentMiddleware):
    """Rate limit model calls."""

    def __init__(self, calls_per_second: float = 1.0):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0

    def wrap_model_call(self, request, handler):
        """Wrap model execution to add rate limiting."""
        # Wait if needed
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        # Execute the actual model call
        self.last_call = time.time()
        return handler(request)

class RetryMiddleware(AgentMiddleware):
    """Retry failed model calls."""

    def wrap_model_call(self, request, handler):
        for attempt in range(3):
            try:
                return handler(request)
            except Exception as e:
                if attempt == 2:  # Last attempt
                    raise
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff

agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[...],
    middleware=[
        RateLimitMiddleware(calls_per_second=2),
        RetryMiddleware(),
    ],
)
```

### Tool Call Wrapper

```python
class ToolLoggingMiddleware(AgentMiddleware):
    """Log all tool executions."""

    def wrap_tool_call(self, request, execute):
        """Wrap tool execution."""
        print(f"Executing tool: {request.tool_call['name']}")
        print(f"With args: {request.tool_call['args']}")

        result = execute(request)

        print(f"Tool result: {result.content[:100]}")
        return result

agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[calculator, search_web],
    middleware=[ToolLoggingMiddleware()],
)
```

### Controlling Flow with jump_to

```python
class ApprovalMiddleware(AgentMiddleware):
    """Require approval before executing certain tools."""

    def before_model(self, state, runtime):
        last_msg = state["messages"][-1]

        # Check if last message was a dangerous tool
        if hasattr(last_msg, "name") and last_msg.name == "delete_database":
            print("⚠️  Dangerous operation detected!")
            approval = input("Approve? (y/n): ")

            if approval.lower() != "y":
                # Stop the agent
                return {"jump_to": "end"}

        return {}

agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[delete_database, create_backup],
    middleware=[ApprovalMiddleware()],
)
```

---

## Structured Output

### Basic Structured Output

```python
from pydantic import BaseModel, Field
from langchain.agents import create_agent

class MovieReview(BaseModel):
    """A movie review."""
    title: str = Field(description="The movie title")
    rating: int = Field(description="Rating from 1-10")
    summary: str = Field(description="Brief review summary")
    would_recommend: bool = Field(description="Would you recommend it?")

agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[],  # No tools needed
    response_format=MovieReview,
)

result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Review the movie 'Inception'"
    }]
})

# Access structured response
review = result["structured_response"]
print(f"Rating: {review.rating}/10")
print(f"Would recommend: {review.would_recommend}")
```

### Structured Output with Tools

```python
from pydantic import BaseModel

class ResearchReport(BaseModel):
    """A research report."""
    topic: str
    key_findings: list[str]
    conclusion: str
    sources: list[str]

agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[search_web, read_webpage],
    response_format=ResearchReport,
    system_prompt="Research the topic thoroughly, then return a structured report"
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Research quantum computing"}]
})

# Agent will:
# 1. Use tools to gather information
# 2. Must return a valid ResearchReport to finish
# 3. Automatically stops when structured response provided

report = result["structured_response"]
for finding in report.key_findings:
    print(f"- {finding}")
```

### Auto-Detection Strategy

```python
# LangChain 1.0 automatically chooses best strategy:
# - If model supports provider-native structured output → Use it
# - Otherwise → Use tool-based approach

agent = create_agent(
    model="openai:gpt-4",  # Supports native JSON mode
    tools=[search_web],
    response_format=MovieReview,  # Automatically uses best approach
)
```

---

## Understanding LangGraph

### What is LangGraph?

**LangGraph is the orchestration framework that powers LangChain 1.0 agents.** It's a separate library that provides stateful, graph-based execution for LLM applications.

Think of it this way:
- **LangChain 1.0** = High-level API for agents (`create_agent`)
- **LangGraph** = Low-level orchestration framework underneath

When you use `create_agent()`, you're actually getting a **LangGraph StateGraph** under the hood.

### The Relationship

```python
from langchain.agents import create_agent

# This looks like a simple LangChain agent
agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[calculator],
)

# But actually, agent is a CompiledStateGraph from LangGraph
print(type(agent))
# Output: <class 'langgraph.graph.state.CompiledStateGraph'>
```

**LangChain 1.0 agents are built on LangGraph.** This is why they have features like:
- Checkpointing (state persistence)
- Streaming (event-based output)
- Interrupts (human-in-the-loop)
- Subgraphs (nested agents)

### What LangGraph Adds

LangGraph provides capabilities that would be very hard to build yourself:

#### 1. **State Management**

```python
# LangGraph manages conversation state automatically
agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[...],
    checkpointer=checkpointer,  # LangGraph feature
)

# State is automatically saved and loaded
config = {"configurable": {"thread_id": "user-123"}}
agent.invoke({"messages": [...]}, config)
```

#### 2. **Event Streaming**

```python
# Stream different types of events
for event in agent.stream(
    {"messages": [{"role": "user", "content": "Calculate 2+2"}]},
    stream_mode="updates"  # LangGraph streaming
):
    print(event)

# Other modes: "values", "messages", "debug"
```

#### 3. **Interrupts (Human-in-the-Loop)**

```python
agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[delete_database],
    interrupt_before=["tools"],  # LangGraph interrupt
    checkpointer=checkpointer,
)

# Execution pauses before tool node
result = agent.invoke({"messages": [...]}, config)

# Get state at interrupt point
state = agent.get_state(config)

# Resume after approval
result = agent.invoke(None, config)  # Continue from interrupt
```

#### 4. **Time Travel Debugging**

```python
# Get history of all states
history = agent.get_state_history(config)

for state in history:
    print(f"Step {state.metadata['step']}")
    print(f"Messages: {len(state.values['messages'])}")
```

#### 5. **Subgraphs (Nested Agents)**

```python
# Create specialized sub-agents
research_agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[search_web, read_webpage],
    name="research_agent",  # Name enables subgraph usage
)

# Use as a tool in parent agent
from langgraph.prebuilt import create_agent_executor

main_agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[calculator, research_agent],  # Sub-agent as tool
)
```

### When to Use LangGraph Directly

**Use `create_agent()`** for most cases:
- ✅ Standard tool-using agents
- ✅ Conversational assistants
- ✅ Research and analysis tasks
- ✅ 90% of agent use cases

**Use LangGraph directly** when you need:
- 🔧 Custom state beyond messages
- 🔧 Complex branching logic
- 🔧 Multiple agent coordination
- 🔧 Custom node behavior
- 🔧 Fine-grained control flow

### Using LangGraph Directly

#### Basic LangGraph Example

```python
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

# Define custom state
class State(TypedDict):
    messages: list
    iteration: int
    summary: str

# Create graph
graph = StateGraph(State)

# Define nodes
def call_model(state: State):
    model = init_chat_model("anthropic:claude-3-sonnet-20240229")
    response = model.invoke(state["messages"])
    return {
        "messages": [response],
        "iteration": state.get("iteration", 0) + 1
    }

def summarize(state: State):
    # Custom logic
    summary = f"Completed in {state['iteration']} iterations"
    return {"summary": summary}

# Add nodes
graph.add_node("model", call_model)
graph.add_node("summarize", summarize)

# Add edges
graph.add_edge(START, "model")
graph.add_edge("model", "summarize")
graph.add_edge("summarize", END)

# Compile
app = graph.compile()

# Use it
result = app.invoke({"messages": [HumanMessage("Hello")]})
print(result["summary"])
```

#### Complex Branching Logic

```python
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class State(TypedDict):
    task: str
    task_type: str
    result: str

def classify_task(state: State):
    """Determine task type."""
    task = state["task"]
    if "calculate" in task.lower() or "math" in task.lower():
        return {"task_type": "math"}
    elif "search" in task.lower() or "find" in task.lower():
        return {"task_type": "search"}
    else:
        return {"task_type": "general"}

def handle_math(state: State):
    return {"result": "Math result"}

def handle_search(state: State):
    return {"result": "Search result"}

def handle_general(state: State):
    return {"result": "General result"}

# Build graph
graph = StateGraph(State)

graph.add_node("classify", classify_task)
graph.add_node("math", handle_math)
graph.add_node("search", handle_search)
graph.add_node("general", handle_general)

# Branching logic
graph.add_edge(START, "classify")

def route_task(state: State) -> str:
    """Route based on task type."""
    return state["task_type"]

graph.add_conditional_edges(
    "classify",
    route_task,
    {
        "math": "math",
        "search": "search",
        "general": "general"
    }
)

graph.add_edge("math", END)
graph.add_edge("search", END)
graph.add_edge("general", END)

app = graph.compile()

# Use it
result = app.invoke({"task": "Calculate 2+2"})
print(result["result"])
```

#### Multi-Agent Coordination

```python
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class MultiAgentState(TypedDict):
    task: str
    research_done: bool
    analysis_done: bool
    final_report: str

def research_agent(state: MultiAgentState):
    """Agent 1: Do research."""
    # Research logic here
    return {"research_done": True}

def analysis_agent(state: MultiAgentState):
    """Agent 2: Analyze research."""
    # Analysis logic here
    return {"analysis_done": True}

def report_generator(state: MultiAgentState):
    """Agent 3: Generate report."""
    report = f"Report based on research and analysis"
    return {"final_report": report}

# Build coordination graph
graph = StateGraph(MultiAgentState)

graph.add_node("research", research_agent)
graph.add_node("analysis", analysis_agent)
graph.add_node("report", report_generator)

graph.add_edge(START, "research")
graph.add_edge("research", "analysis")
graph.add_edge("analysis", "report")
graph.add_edge("report", END)

app = graph.compile()

result = app.invoke({"task": "Analyze market trends"})
print(result["final_report"])
```

### LangGraph Features Deep Dive

#### Checkpointing in Detail

```python
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph, START, END

# Create checkpointer
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost/db"
)

# Build graph
graph = StateGraph(State)
# ... add nodes and edges ...

# Compile with checkpointer
app = graph.compile(checkpointer=checkpointer)

# Every step is automatically checkpointed
config = {"configurable": {"thread_id": "task-123"}}
result = app.invoke({"messages": [...]}, config)

# Get current state
state = app.get_state(config)
print(f"Current values: {state.values}")
print(f"Next nodes: {state.next}")

# Get full history
for historical_state in app.get_state_history(config):
    print(f"Step: {historical_state.metadata['step']}")
    print(f"Values: {historical_state.values}")
```

#### Stream Modes

```python
# Mode 1: "values" - Full state after each node
for event in app.stream(input_data, stream_mode="values"):
    print(f"Complete state: {event}")

# Mode 2: "updates" - Only what changed
for event in app.stream(input_data, stream_mode="updates"):
    print(f"Updates: {event}")

# Mode 3: "messages" - Just message events
for event in app.stream(input_data, stream_mode="messages"):
    print(f"Message: {event}")

# Mode 4: "debug" - Everything including internal events
for event in app.stream(input_data, stream_mode="debug"):
    print(f"Debug: {event}")

# Multiple modes at once
for event in app.stream(
    input_data,
    stream_mode=["values", "messages"]
):
    print(event)
```

#### Dynamic Interrupts

```python
from langgraph.types import interrupt

def potentially_dangerous_node(state: State):
    """Node that might need approval."""
    action = state["proposed_action"]

    if action == "delete_database":
        # Interrupt and wait for approval
        approval = interrupt(
            {
                "action": action,
                "reason": "This is a dangerous operation"
            }
        )

        if not approval:
            return {"result": "Action cancelled"}

    # Proceed with action
    return {"result": f"Executed: {action}"}

# Use the graph
result = app.invoke({"proposed_action": "delete_database"}, config)

# Execution is paused, get interrupt value
state = app.get_state(config)
interrupt_data = state.tasks[0].interrupts[0].value

# Resume with approval
result = app.invoke(
    {"approval": True},  # Resume data
    config,
    resume_from="potentially_dangerous_node"
)
```

### Installing LangGraph

LangGraph is automatically installed with LangChain 1.0, but you can also install it directly:

```bash
# Already included with langchain 1.0
pip install langchain==1.0.0a15

# Or install separately
pip install langgraph

# Checkpointer backends
pip install langgraph-checkpoint-postgres  # PostgreSQL
pip install langgraph-checkpoint-sqlite   # SQLite
```

### LangChain vs LangGraph Decision Tree

```
Start
  │
  ├─ Need standard tool-using agent?
  │  └─> Use `create_agent()` ✅
  │
  ├─ Need conversational assistant?
  │  └─> Use `create_agent()` with checkpointer ✅
  │
  ├─ Need custom state beyond messages?
  │  └─> Use LangGraph directly 🔧
  │
  ├─ Need complex branching logic?
  │  └─> Use LangGraph directly 🔧
  │
  ├─ Need to coordinate multiple agents?
  │  └─> Use LangGraph directly 🔧
  │
  └─ Need fine-grained node control?
     └─> Use LangGraph directly 🔧
```

### Real-World Example: Custom State

```python
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

# Custom state with business logic
class CustomerSupportState(TypedDict):
    messages: list
    customer_id: str
    issue_type: str
    priority: int
    resolution_steps: list[str]
    resolved: bool

def classify_issue(state: CustomerSupportState):
    """Classify the customer issue."""
    # Use LLM to classify
    model = init_chat_model("anthropic:claude-3-sonnet-20240229")

    classification_prompt = f"""
    Customer message: {state['messages'][-1].content}

    Classify this issue type (billing, technical, account)
    and priority (1-5):
    """

    response = model.invoke([HumanMessage(classification_prompt)])

    # Parse response (simplified)
    return {
        "issue_type": "technical",  # parsed from response
        "priority": 3,
        "resolution_steps": []
    }

def route_to_specialist(state: CustomerSupportState):
    """Route to appropriate handler."""
    if state["priority"] >= 4:
        return "escalation"
    elif state["issue_type"] == "billing":
        return "billing"
    else:
        return "technical"

def handle_billing(state: CustomerSupportState):
    """Handle billing issues."""
    steps = ["Check account", "Review charges", "Process refund"]
    return {
        "resolution_steps": steps,
        "resolved": True
    }

def handle_technical(state: CustomerSupportState):
    """Handle technical issues."""
    steps = ["Run diagnostics", "Clear cache", "Restart service"]
    return {
        "resolution_steps": steps,
        "resolved": True
    }

def escalate(state: CustomerSupportState):
    """Escalate to senior support."""
    return {
        "resolution_steps": ["Escalated to senior support"],
        "resolved": False
    }

# Build graph
graph = StateGraph(CustomerSupportState)

graph.add_node("classify", classify_issue)
graph.add_node("billing", handle_billing)
graph.add_node("technical", handle_technical)
graph.add_node("escalation", escalate)

graph.add_edge(START, "classify")
graph.add_conditional_edges(
    "classify",
    route_to_specialist,
    {
        "billing": "billing",
        "technical": "technical",
        "escalation": "escalation"
    }
)

graph.add_edge("billing", END)
graph.add_edge("technical", END)
graph.add_edge("escalation", END)

app = graph.compile(checkpointer=checkpointer)

# Use it
result = app.invoke({
    "messages": [HumanMessage("I was charged twice!")],
    "customer_id": "CUST-123"
}, config)

print(f"Issue type: {result['issue_type']}")
print(f"Priority: {result['priority']}")
print(f"Steps: {result['resolution_steps']}")
```

### Key Takeaways

1. **LangChain 1.0 = High-level** - Use `create_agent()` for most cases
2. **LangGraph = Low-level** - Use directly for complex orchestration
3. **Agents are graphs** - Every `create_agent()` returns a LangGraph
4. **Start high, go low** - Begin with `create_agent()`, drop to LangGraph when needed
5. **State is flexible** - LangGraph lets you define any state structure
6. **Checkpointing is powerful** - Free persistence, time travel, interrupts

### Learning Path

1. **Week 1**: Use `create_agent()` exclusively
2. **Week 2**: Explore checkpointing and streaming
3. **Week 3**: Add interrupts for approval workflows
4. **Week 4**: Try simple LangGraph for custom state
5. **Month 2+**: Build complex multi-agent systems with LangGraph

**Remember**: Most applications never need direct LangGraph usage. Start with `create_agent()` and only drop to LangGraph when you hit its limitations.

---

## Production Patterns

### Complete Production Agent

```python
from langchain.agents import create_agent, AgentMiddleware
from langgraph.checkpoint.postgres import PostgresSaver
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Middleware for production
class ProductionMiddleware(AgentMiddleware):
    """Production-grade middleware with logging, metrics, error handling."""

    def before_model(self, state, runtime):
        logger.info(f"Model call with {len(state['messages'])} messages")
        return {}

    def after_model(self, state, runtime):
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            logger.info(f"Model requested {len(last_msg.tool_calls)} tool calls")
        return {}

    def wrap_model_call(self, request, handler):
        try:
            result = handler(request)
            logger.info("Model call successful")
            return result
        except Exception as e:
            logger.error(f"Model call failed: {e}")
            raise

# Define tools
@tool
def search_database(query: str) -> str:
    """Search internal database."""
    # Real implementation here
    return f"Database results for: {query}"

@tool
def query_api(endpoint: str) -> str:
    """Query external API."""
    # Real implementation here
    return f"API results from: {endpoint}"

# Create production agent
def create_production_agent(
    model: str = "anthropic:claude-3-sonnet-20240229",
    db_url: Optional[str] = None
):
    """Create a production-ready agent."""

    # Setup checkpointer
    checkpointer = None
    if db_url:
        checkpointer = PostgresSaver.from_conn_string(db_url)

    agent = create_agent(
        model=model,
        tools=[search_database, query_api],
        system_prompt="""You are a helpful assistant with access to internal tools.

        Guidelines:
        - Use tools to gather accurate information
        - Provide clear, concise answers
        - If you cannot answer, explain why
        - Always cite your sources""",
        middleware=[ProductionMiddleware()],
        checkpointer=checkpointer,
        interrupt_before=["tools"],  # Allow approval of tool calls
        debug=False,  # Disable in production
    )

    return agent

# Use in production
agent = create_production_agent(
    model="anthropic:claude-3-sonnet-20240229",
    db_url="postgresql://user:pass@localhost/db"
)

# Handle requests
def handle_request(user_id: str, message: str):
    config = {"configurable": {"thread_id": f"user-{user_id}"}}

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config=config
        )
        return result["messages"][-1].content
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return "I apologize, but I encountered an error. Please try again."
```

### Error Handling Patterns

```python
from langgraph.errors import GraphRecursionError

def safe_agent_call(agent, message: str, user_id: str):
    """Safely call agent with comprehensive error handling."""
    config = {"configurable": {"thread_id": f"user-{user_id}"}}

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
            {"recursion_limit": 15}
        )
        return {
            "success": True,
            "response": result["messages"][-1].content,
            "structured_response": result.get("structured_response")
        }

    except GraphRecursionError:
        logger.error("Agent exceeded recursion limit")
        return {
            "success": False,
            "error": "too_many_iterations",
            "message": "The request is taking too long. Please try a simpler question."
        }

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "success": False,
            "error": "internal_error",
            "message": "An unexpected error occurred. Please try again."
        }
```

---

## Common Pitfalls

### 1. Forgetting to Pin Versions

❌ **Don't do this:**
```txt
# requirements.txt
langchain>=1.0.0a1
```

✅ **Do this:**
```txt
# requirements.txt
langchain==1.0.0a15
langchain-core==1.0.0rc1
```

### 2. Not Providing Clear System Prompts

❌ **Vague:**
```python
agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[search_web, calculator],
    system_prompt="You are helpful"
)
# Agent might not know when to use which tool or when to stop
```

✅ **Clear:**
```python
agent = create_agent(
    model="anthropic:claude-3-sonnet-20240229",
    tools=[search_web, calculator],
    system_prompt="""You are a research assistant.

Use search_web to find information online.
Use calculator for mathematical operations.

When you have sufficient information, provide a complete answer and STOP.
Do not ask follow-up questions."""
)
```

### 3. No Recursion Limit

❌ **No safety valve:**
```python
agent.invoke({"messages": [...]})
# Could run forever if agent gets stuck
```

✅ **With safety valve:**
```python
agent.invoke(
    {"messages": [...]},
    {"recursion_limit": 15}
)
```

### 4. Ignoring Tool Docstrings

❌ **Bad:**
```python
def search_web(query):
    return search(query)
```

✅ **Good:**
```python
def search_web(query: str) -> str:
    """Search the web for information.

    Args:
        query: The search query string

    Returns:
        Search results as a string
    """
    return search(query)
```

The model reads docstrings to understand when/how to use tools!

### 5. Not Handling Thread IDs Properly

❌ **Same thread for all users:**
```python
config = {"configurable": {"thread_id": "default"}}
agent.invoke({"messages": [...]}, config)
# All users share conversation history!
```

✅ **Unique thread per user:**
```python
config = {"configurable": {"thread_id": f"user-{user_id}"}}
agent.invoke({"messages": [...]}, config)
```

---

## Quick Reference

### Model Calling
```python
from langchain.chat_models import init_chat_model
model = init_chat_model("provider:model-name")
response = model.invoke([HumanMessage("Hello")])
```

### Simple Agent
```python
from langchain.agents import create_agent
agent = create_agent(model="...", tools=[...])
result = agent.invoke({"messages": [{"role": "user", "content": "..."}]})
```

### With Memory
```python
from langgraph.checkpoint.memory import MemorySaver
agent = create_agent(
    model="...",
    tools=[...],
    checkpointer=MemorySaver()
)
config = {"configurable": {"thread_id": "user-123"}}
result = agent.invoke({"messages": [...]}, config)
```

### Structured Output
```python
from pydantic import BaseModel
class Response(BaseModel):
    answer: str
    confidence: float

agent = create_agent(
    model="...",
    tools=[...],
    response_format=Response
)
result = agent.invoke({"messages": [...]})
structured = result["structured_response"]
```

---

## Next Steps

1. Start with simple model calling (`init_chat_model`)
2. Add tools when you need the model to "do things"
3. Use agents when you need automatic tool orchestration
4. Add checkpointer when you need conversation memory
5. Use middleware for cross-cutting concerns
6. Add structured output when you need typed responses

**Remember:** Start simple, add complexity only when you need it.

---

**LangChain 1.0 Documentation:** https://docs.langchain.com/
**GitHub Issues:** https://github.com/langchain-ai/langchain/issues
**Discord Community:** https://discord.gg/langchain
