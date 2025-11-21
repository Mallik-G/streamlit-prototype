# Workflow Executors - Pluggable Architecture

The workflow execution engine is designed to be **pluggable** - you can swap orchestration strategies without changing workflow definitions.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Definition (YAML)                │
│  - Platform-agnostic format                                  │
│  - Describes what to do, not how                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              WorkflowExecutorRegistry                        │
│  - Manages available executors                               │
│  - Routes workflow to appropriate engine                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Default    │  │   CrewAI     │  │  LangGraph   │
│   Executor   │  │   Executor   │  │   Executor   │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Current Executors

### 1. Default Executor (Built-in)
**Status:** ✅ Active
**File:** `workflow_builder.py`

**Features:**
- Simple, transparent execution
- Sequential, Parallel, DAG modes
- Variable passing via shared context
- No external dependencies
- Best for most use cases

**Pros:**
- Easy to understand and debug
- No learning curve
- Predictable behavior
- YAML-based, version controllable

**Cons:**
- No advanced agent collaboration
- No dynamic task routing
- Simplified parallelism (TODO: implement true async)

### 2. CrewAI Executor (Example)
**Status:** 🚧 Example implementation
**File:** `workflow_executors_example.py`

**Features:**
- Hierarchical agent roles
- Built-in agent communication
- Automatic task delegation
- CrewAI framework integration

**When to use:**
- Need agent-to-agent collaboration
- Complex multi-role workflows
- Research-heavy tasks
- Dynamic task routing

**Installation:**
```bash
pip install crewai crewai-tools
```

### 3. LangGraph Executor (Example)
**Status:** 🚧 Example implementation
**File:** `workflow_executors_example.py`

**Features:**
- State machine-based execution
- Conditional branching
- Cyclic workflows (loops)
- Checkpointing and resume

**When to use:**
- Need conditional logic
- Complex state management
- Workflow loops/iterations
- Error recovery with checkpoints

**Installation:**
```bash
pip install langgraph
```

### 4. Async Executor (Example)
**Status:** 🚧 Example implementation
**File:** `workflow_executors_example.py`

**Features:**
- True parallel execution with asyncio
- Concurrent step processing
- Better resource utilization

**When to use:**
- Many independent steps
- I/O-bound workflows
- Need maximum parallelism

## Creating a Custom Executor

### Step 1: Implement the Base Class

```python
from workflow_builder import WorkflowExecutorBase
from typing import Dict, Any

class MyCustomExecutor(WorkflowExecutorBase):
    """Your custom executor implementation"""

    def execute(self) -> Dict[str, Any]:
        """
        Execute workflow and return results.

        Returns:
            Dict with keys:
            - success: bool
            - results: Dict[step_id, step_result]
            - context: Dict[variable_name, value]
        """
        # Your custom orchestration logic here

        # Access workflow definition
        for step in self.workflow.steps:
            print(f"Step: {step.name}")
            print(f"Agent: {step.agent_id}")
            print(f"Task: {step.task_description}")

        # Build prompts with context
        prompt = self._build_prompt(step)

        # Return results
        return {
            "success": True,
            "results": self.step_results,
            "context": self.context
        }
```

### Step 2: Register Your Executor

```python
from workflow_builder import WorkflowExecutorRegistry

# Register your executor
WorkflowExecutorRegistry.register("myexecutor", MyCustomExecutor)
```

### Step 3: Use Your Executor

**In Code:**
```python
from workflow_builder import WorkflowBuilder, WorkflowExecutorRegistry

# Load workflow
builder = WorkflowBuilder()
workflow = builder.load_workflow("workflow-id")

# Use your executor
executor = WorkflowExecutorRegistry.get_executor("myexecutor", workflow)
result = executor.execute()
```

**In Streamlit UI:**
- Your executor will automatically appear in the "Execution Engine" dropdown
- Users can select it when executing workflows

## Design Principles

### 1. Separation of Concerns
- **Workflow Definition (YAML)**: What to do
- **Executor**: How to do it

This allows:
- Same workflow, different execution strategies
- Easy testing and comparison
- Future-proof architecture

### 2. Backward Compatibility
```python
# Old code still works
executor = WorkflowExecutor(workflow)

# New code uses registry
executor = WorkflowExecutorRegistry.get_executor("default", workflow)
```

### 3. Discoverability
```python
# List all available executors
executors = WorkflowExecutorRegistry.list_executors()
# => ['default', 'crewai', 'langgraph', 'myexecutor']
```

## Workflow Definition Format

Executors receive a `WorkflowConfig` object:

```python
@dataclass
class WorkflowConfig:
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    execution_mode: str  # sequential, parallel, dag
    # ... metadata
```

```python
@dataclass
class WorkflowStep:
    id: str
    name: str
    agent_id: str
    task_description: str
    input_variables: List[str]  # Variables from previous steps
    output_variable: str        # Variable to save result to
    platform_tools: List[str]   # UC Functions / UDFs
    depends_on: List[str]       # Dependencies (for DAG mode)
```

## Best Practices

### 1. Keep Definitions Engine-Agnostic
✅ **Good:**
```yaml
steps:
  - name: "Research"
    agent_id: "researcher-001"
    task: "Research topic X"
    output_variable: "findings"
```

❌ **Bad:**
```yaml
steps:
  - name: "Research"
    crewai_role: "Researcher"  # CrewAI-specific
    langgraph_state: "research_state"  # LangGraph-specific
```

### 2. Use Standard Return Format
All executors should return:
```python
{
    "success": bool,
    "results": {
        "step-id-1": {"success": True, "output": "..."},
        "step-id-2": {"success": True, "output": "..."}
    },
    "context": {
        "variable1": "value1",
        "variable2": "value2"
    }
}
```

### 3. Handle Errors Gracefully
```python
def execute(self) -> Dict[str, Any]:
    try:
        # Your execution logic
        return {"success": True, ...}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": self.step_results,
            "context": self.context
        }
```

## Migration Guide

### From Kasal (CrewAI)
If you're migrating from Kasal:

1. **Convert Crew definitions to Workflows:**
   - Kasal Agents → Our Agents (via Agent Builder)
   - Kasal Tasks → Workflow Steps
   - Crew → Workflow

2. **Use CrewAI Executor:**
   ```python
   WorkflowExecutorRegistry.register("crewai", CrewAIExecutor)
   executor = WorkflowExecutorRegistry.get_executor("crewai", workflow)
   ```

3. **Or use Default Executor:**
   - Simpler, more transparent
   - Same workflow definition
   - Easier to debug

## Future Enhancements

Planned executor implementations:

- [ ] **AsyncWorkflowExecutor**: True parallel execution with asyncio
- [ ] **DAGExecutor**: Proper topological sort with parallelism
- [ ] **RetryExecutor**: Automatic retry with exponential backoff
- [ ] **CachedExecutor**: Cache step results for faster re-execution
- [ ] **StreamingExecutor**: Real-time streaming of intermediate results

## FAQs

**Q: Should I use CrewAI or the default executor?**
A: Start with default. It's simpler and works for 90% of use cases. Use CrewAI only if you need advanced agent collaboration.

**Q: Can I mix executors in one workflow?**
A: No. Each workflow execution uses one executor. But you can execute the same workflow with different executors to compare.

**Q: How do I debug a custom executor?**
A: Add print statements, use Python debugger, or log to files. The workflow definition is just a dataclass, easy to inspect.

**Q: Will my workflows break if I change executors?**
A: No. Workflow definitions are executor-agnostic. Same YAML works with any executor (assuming they support the same execution modes).

**Q: Can I create an executor that calls external APIs?**
A: Yes! Implement `WorkflowExecutorBase` and call any service you want (AWS Step Functions, Temporal, etc.).

## Resources

- **Code Examples**: `workflow_executors_example.py`
- **Base Class**: `workflow_builder.py` → `WorkflowExecutorBase`
- **Registry**: `workflow_builder.py` → `WorkflowExecutorRegistry`
- **UI Integration**: `pages/5_📊_Workflow_Builder.py`

## Support

For questions or contributions:
- Open an issue on GitHub
- Check `workflow_executors_example.py` for working examples
- Read the base class docstrings in `workflow_builder.py`
