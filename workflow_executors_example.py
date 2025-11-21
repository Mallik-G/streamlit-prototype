"""
Example: Custom Workflow Executors

This file demonstrates how to create custom workflow executors
to plug in different orchestration engines (CrewAI, LangGraph, etc.)

The workflow engine is designed to be pluggable - you can swap
orchestration strategies without changing workflow definitions (YAML).
"""

from workflow_builder import (
    WorkflowExecutorBase,
    WorkflowExecutorRegistry,
    WorkflowConfig
)
from typing import Dict, Any


# ============================================================================
# Example 1: CrewAI Executor (Conceptual - requires crewai package)
# ============================================================================

class CrewAIExecutor(WorkflowExecutorBase):
    """
    CrewAI-based workflow executor.
    Uses CrewAI's agent collaboration framework.

    Install: pip install crewai crewai-tools

    Features:
    - Hierarchical agent roles (Manager, Worker)
    - Built-in agent communication
    - Automatic task delegation
    """

    def execute(self) -> Dict[str, Any]:
        """Execute workflow using CrewAI"""
        try:
            from crewai import Crew, Agent, Task, Process
            from agent_builder import AgentBuilder
        except ImportError:
            return {
                "success": False,
                "error": "CrewAI not installed. Run: pip install crewai"
            }

        builder = AgentBuilder()

        # Convert our agents to CrewAI agents
        crew_agents = []
        crew_tasks = []

        for step in self.workflow.steps:
            # Load our agent config
            agent_config = builder.load_agent(step.agent_id)
            if not agent_config:
                continue

            # Create CrewAI agent
            crew_agent = Agent(
                role=step.name,
                goal=step.task_description,
                backstory=agent_config.system_prompt,
                verbose=True,
                allow_delegation=True if self.workflow.execution_mode == "dag" else False
            )
            crew_agents.append(crew_agent)

            # Create CrewAI task
            task = Task(
                description=step.task_description,
                agent=crew_agent,
                expected_output=step.output_variable or "result"
            )
            crew_tasks.append(task)

        # Create and run crew
        process = {
            "sequential": Process.sequential,
            "parallel": Process.sequential,  # CrewAI doesn't have true parallel
            "dag": Process.hierarchical
        }.get(self.workflow.execution_mode, Process.sequential)

        crew = Crew(
            agents=crew_agents,
            tasks=crew_tasks,
            process=process,
            verbose=True
        )

        # Execute
        result = crew.kickoff()

        return {
            "success": True,
            "results": {"crew_output": result},
            "context": {"final_output": str(result)}
        }


# ============================================================================
# Example 2: LangGraph Executor (Conceptual - requires langgraph package)
# ============================================================================

class LangGraphExecutor(WorkflowExecutorBase):
    """
    LangGraph-based workflow executor.
    Uses state machine for complex conditional workflows.

    Install: pip install langgraph

    Features:
    - State machine-based execution
    - Conditional branching
    - Cyclic workflows (loops)
    - Checkpointing and resume
    """

    def execute(self) -> Dict[str, Any]:
        """Execute workflow using LangGraph"""
        try:
            from langgraph.graph import StateGraph
            from agent_builder import AgentBuilder, AgentExecutor
        except ImportError:
            return {
                "success": False,
                "error": "LangGraph not installed. Run: pip install langgraph"
            }

        builder = AgentBuilder()

        # Define state
        from typing import TypedDict

        class WorkflowState(TypedDict):
            context: Dict[str, Any]
            current_step: int
            results: Dict[str, Any]

        # Create graph
        graph = StateGraph(WorkflowState)

        # Add nodes for each step
        for idx, step in enumerate(self.workflow.steps):
            def create_node(step_config):
                def node_fn(state: WorkflowState) -> WorkflowState:
                    agent = builder.load_agent(step_config.agent_id)
                    if not agent:
                        return state

                    prompt = self._build_prompt(step_config)
                    executor = AgentExecutor(agent)

                    response = ""
                    for chunk in executor.execute(prompt):
                        response += chunk

                    # Update state
                    state["results"][step_config.id] = response
                    if step_config.output_variable:
                        state["context"][step_config.output_variable] = response
                    state["current_step"] = state.get("current_step", 0) + 1

                    return state

                return node_fn

            graph.add_node(step.id, create_node(step))

        # Add edges based on execution mode
        if self.workflow.execution_mode == "sequential":
            for i in range(len(self.workflow.steps) - 1):
                graph.add_edge(
                    self.workflow.steps[i].id,
                    self.workflow.steps[i + 1].id
                )
        elif self.workflow.execution_mode == "dag":
            for step in self.workflow.steps:
                for dep in step.depends_on:
                    graph.add_edge(dep, step.id)

        # Set entry point
        graph.set_entry_point(self.workflow.steps[0].id)

        # Compile and execute
        app = graph.compile()
        initial_state = {
            "context": self.context,
            "current_step": 0,
            "results": {}
        }

        final_state = app.invoke(initial_state)

        return {
            "success": True,
            "results": final_state.get("results", {}),
            "context": final_state.get("context", {})
        }


# ============================================================================
# Example 3: Async Executor (True parallel execution)
# ============================================================================

class AsyncWorkflowExecutor(WorkflowExecutorBase):
    """
    Async workflow executor for true parallel execution.
    Uses Python asyncio for concurrent step execution.
    """

    def execute(self) -> Dict[str, Any]:
        """Execute workflow with asyncio"""
        import asyncio

        if self.workflow.execution_mode == "sequential":
            return self._execute_sequential()
        elif self.workflow.execution_mode == "parallel":
            return asyncio.run(self._execute_parallel_async())
        elif self.workflow.execution_mode == "dag":
            return asyncio.run(self._execute_dag_async())

    def _execute_sequential(self) -> Dict[str, Any]:
        """Sequential execution (no async needed)"""
        from agent_builder import AgentBuilder, AgentExecutor

        builder = AgentBuilder()

        for step in self.workflow.steps:
            agent = builder.load_agent(step.agent_id)
            if not agent:
                continue

            prompt = self._build_prompt(step)
            executor = AgentExecutor(agent)

            response = ""
            for chunk in executor.execute(prompt):
                response += chunk

            self.step_results[step.id] = {"success": True, "output": response}
            if step.output_variable:
                self.context[step.output_variable] = response

        return {
            "success": True,
            "results": self.step_results,
            "context": self.context
        }

    async def _execute_parallel_async(self) -> Dict[str, Any]:
        """True parallel execution with asyncio"""
        from agent_builder import AgentBuilder, AgentExecutor
        import asyncio

        builder = AgentBuilder()

        async def execute_step(step):
            agent = builder.load_agent(step.agent_id)
            if not agent:
                return step.id, {"success": False, "error": "Agent not found"}

            prompt = self._build_prompt(step)
            executor = AgentExecutor(agent)

            response = ""
            # Note: Would need async version of execute
            for chunk in executor.execute(prompt):
                response += chunk
                await asyncio.sleep(0)  # Yield control

            return step.id, {"success": True, "output": response}

        # Execute all steps in parallel
        tasks = [execute_step(step) for step in self.workflow.steps]
        results = await asyncio.gather(*tasks)

        # Collect results
        for step_id, result in results:
            self.step_results[step_id] = result

        return {
            "success": True,
            "results": self.step_results,
            "context": self.context
        }

    async def _execute_dag_async(self) -> Dict[str, Any]:
        """DAG execution with topological sort and parallelism"""
        # TODO: Implement topological sort and async execution
        return await self._execute_parallel_async()


# ============================================================================
# Registration Examples
# ============================================================================

def register_all_executors():
    """Register all available executors"""

    # Register CrewAI executor
    try:
        WorkflowExecutorRegistry.register("crewai", CrewAIExecutor)
        print("✓ CrewAI executor registered")
    except Exception as e:
        print(f"✗ CrewAI executor not available: {e}")

    # Register LangGraph executor
    try:
        WorkflowExecutorRegistry.register("langgraph", LangGraphExecutor)
        print("✓ LangGraph executor registered")
    except Exception as e:
        print(f"✗ LangGraph executor not available: {e}")

    # Register Async executor
    try:
        WorkflowExecutorRegistry.register("async", AsyncWorkflowExecutor)
        print("✓ Async executor registered")
    except Exception as e:
        print(f"✗ Async executor not available: {e}")


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    """
    Example usage of custom executors
    """
    from workflow_builder import WorkflowBuilder

    # Register executors
    register_all_executors()

    # List available executors
    print("\nAvailable executors:", WorkflowExecutorRegistry.list_executors())

    # Load a workflow
    builder = WorkflowBuilder()
    workflows = builder.list_workflows()

    if workflows:
        workflow = workflows[0]

        # Execute with default executor
        print("\n=== Executing with Default Executor ===")
        executor = WorkflowExecutorRegistry.get_executor("default", workflow)
        result = executor.execute()
        print("Result:", result.get("success"))

        # Execute with async executor (if available)
        if "async" in WorkflowExecutorRegistry.list_executors():
            print("\n=== Executing with Async Executor ===")
            executor = WorkflowExecutorRegistry.get_executor("async", workflow)
            result = executor.execute()
            print("Result:", result.get("success"))

        # Execute with CrewAI (if available)
        if "crewai" in WorkflowExecutorRegistry.list_executors():
            print("\n=== Executing with CrewAI Executor ===")
            executor = WorkflowExecutorRegistry.get_executor("crewai", workflow)
            result = executor.execute()
            print("Result:", result.get("success"))
    else:
        print("No workflows found. Create one first!")


# ============================================================================
# How to Use in Streamlit UI
# ============================================================================

"""
In pages/5_📊_Workflow_Builder.py, add executor selection:

```python
# In the workflow execution section
executor_type = st.selectbox(
    "Execution Engine",
    options=WorkflowExecutorRegistry.list_executors(),
    help="Select workflow orchestration engine"
)

# Get appropriate executor
executor = WorkflowExecutorRegistry.get_executor(executor_type, workflow)
result = executor.execute()
```
"""
