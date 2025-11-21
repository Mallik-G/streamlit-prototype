"""
Workflow Builder - Multi-Agent Workflow Orchestration
Form-based configuration, YAML storage, Mermaid visualization

Architecture:
- Pluggable executor design: Swap orchestration engines (Default, CrewAI, LangGraph)
- Workflow definition (YAML) is engine-agnostic
- Register custom executors via WorkflowExecutorRegistry
"""
import os
import yaml
import json
from typing import List, Dict, Any, Optional, Type
from dataclasses import dataclass, field, asdict
from datetime import datetime
from abc import ABC, abstractmethod
import uuid
import logging

# Import logging utilities
try:
    from utils.logging_config import (
        get_logger,
        get_performance_logger,
        get_audit_logger,
        get_debug_context,
    )

    logger = get_logger("workflow_builder")
    perf_logger = get_performance_logger()
    audit_logger = get_audit_logger()
    debug = get_debug_context()
except ImportError:
    # Fallback if logging not available
    logger = logging.getLogger("workflow_builder")
    perf_logger = None
    audit_logger = None
    debug = None


@dataclass
class WorkflowStep:
    """A single step in a workflow"""
    id: str
    name: str
    agent_id: str
    task_description: str
    input_variables: List[str] = field(default_factory=list)
    output_variable: str = ""
    platform_tools: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    timeout: int = 300  # seconds
    retry: int = 0


@dataclass
class WorkflowConfig:
    """Complete workflow configuration"""
    id: str
    name: str
    description: str
    creator: str
    created_at: str
    updated_at: str
    steps: List[WorkflowStep]
    execution_mode: str = "sequential"  # sequential, parallel, dag
    tags: List[str] = field(default_factory=list)
    is_public: bool = False
    category: str = "general"
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert WorkflowStep objects to dicts
        data['steps'] = [asdict(step) for step in self.steps]
        return data

    def to_yaml(self) -> str:
        """Convert to YAML string"""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowConfig':
        """Create from dictionary"""
        steps_data = data.pop('steps', [])
        steps = [WorkflowStep(**step) for step in steps_data]
        return cls(steps=steps, **data)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'WorkflowConfig':
        """Create from YAML string"""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)

    def to_mermaid(self) -> str:
        """Generate Mermaid diagram from workflow"""
        lines = ["graph TD"]

        # Add nodes
        for step in self.steps:
            node_id = step.id.replace('-', '_')
            label = f"{step.name}<br/>{step.task_description[:30]}..."
            lines.append(f'    {node_id}["{label}"]')

        # Add edges based on execution mode
        if self.execution_mode == "sequential":
            for i in range(len(self.steps) - 1):
                from_id = self.steps[i].id.replace('-', '_')
                to_id = self.steps[i + 1].id.replace('-', '_')

                # Add output variable as edge label
                output_var = self.steps[i].output_variable
                label = f"|{output_var}|" if output_var else ""
                lines.append(f'    {from_id} -->{label} {to_id}')

        elif self.execution_mode == "dag":
            # Use depends_on relationships
            for step in self.steps:
                step_id = step.id.replace('-', '_')
                for dep in step.depends_on:
                    dep_id = dep.replace('-', '_')

                    # Find output variable from dependency
                    dep_step = next((s for s in self.steps if s.id == dep), None)
                    label = f"|{dep_step.output_variable}|" if dep_step and dep_step.output_variable else ""

                    lines.append(f'    {dep_id} -->{label} {step_id}')

        elif self.execution_mode == "parallel":
            # All steps run in parallel from start
            lines.append('    Start([Start])')
            lines.append('    End([End])')
            for step in self.steps:
                step_id = step.id.replace('-', '_')
                lines.append(f'    Start --> {step_id}')
                lines.append(f'    {step_id} --> End')

        # Add styling
        lines.append('    classDef default fill:#29B5E8,stroke:#249EBF,stroke-width:2px,color:#fff')

        return '\n'.join(lines)


class WorkflowBuilder:
    """Manage workflow creation and storage"""

    def __init__(self, storage_path: str = "workflows"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def create_workflow(
        self,
        name: str,
        description: str,
        steps: List[WorkflowStep],
        execution_mode: str = "sequential",
        creator: str = "anonymous",
        tags: List[str] = None,
        category: str = "general",
        is_public: bool = False
    ) -> WorkflowConfig:
        """Create a new workflow"""
        workflow_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        workflow = WorkflowConfig(
            id=workflow_id,
            name=name,
            description=description,
            creator=creator,
            created_at=now,
            updated_at=now,
            steps=steps,
            execution_mode=execution_mode,
            tags=tags or [],
            category=category,
            is_public=is_public,
            version="1.0.0"
        )

        self.save_workflow(workflow)
        return workflow

    def save_workflow(self, workflow: WorkflowConfig):
        """Save workflow as YAML file"""
        file_path = os.path.join(self.storage_path, f"{workflow.id}.yaml")
        with open(file_path, 'w') as f:
            f.write(workflow.to_yaml())

    def load_workflow(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """Load workflow from YAML file"""
        file_path = os.path.join(self.storage_path, f"{workflow_id}.yaml")
        if not os.path.exists(file_path):
            return None

        with open(file_path, 'r') as f:
            yaml_str = f.read()
            return WorkflowConfig.from_yaml(yaml_str)

    def list_workflows(
        self,
        creator: str = None,
        category: str = None,
        tags: List[str] = None,
        public_only: bool = False
    ) -> List[WorkflowConfig]:
        """List all workflows with optional filters"""
        workflows = []

        for filename in os.listdir(self.storage_path):
            if not filename.endswith('.yaml'):
                continue

            with open(os.path.join(self.storage_path, filename), 'r') as f:
                workflow = WorkflowConfig.from_yaml(f.read())

                # Apply filters
                if public_only and not workflow.is_public:
                    continue
                if creator and workflow.creator != creator:
                    continue
                if category and workflow.category != category:
                    continue
                if tags and not any(tag in workflow.tags for tag in tags):
                    continue

                workflows.append(workflow)

        # Sort by updated_at descending
        workflows.sort(key=lambda x: x.updated_at, reverse=True)
        return workflows

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow"""
        file_path = os.path.join(self.storage_path, f"{workflow_id}.yaml")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def export_workflow(self, workflow_id: str, format: str = "yaml") -> str:
        """Export workflow in specified format"""
        workflow = self.load_workflow(workflow_id)
        if not workflow:
            return ""

        if format == "yaml":
            return workflow.to_yaml()
        elif format == "json":
            return json.dumps(workflow.to_dict(), indent=2)
        elif format == "mermaid":
            return workflow.to_mermaid()
        else:
            return ""

    def import_workflow(self, content: str, format: str = "yaml") -> Optional[WorkflowConfig]:
        """Import workflow from YAML or JSON"""
        try:
            if format == "yaml":
                workflow = WorkflowConfig.from_yaml(content)
            elif format == "json":
                data = json.loads(content)
                workflow = WorkflowConfig.from_dict(data)
            else:
                return None

            # Generate new ID for imported workflow
            workflow.id = str(uuid.uuid4())
            workflow.created_at = datetime.now().isoformat()
            workflow.updated_at = workflow.created_at

            self.save_workflow(workflow)
            return workflow

        except Exception as e:
            print(f"Error importing workflow: {e}")
            return None


class WorkflowExecutorBase(ABC):
    """
    Abstract base class for workflow executors.
    Implement this to create custom orchestration engines (CrewAI, LangGraph, etc.)
    """

    def __init__(self, workflow: WorkflowConfig):
        self.workflow = workflow
        self.context = {}  # Shared context for variables
        self.step_results = {}

    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        Execute workflow and return results.

        Returns:
            Dict with keys:
            - success: bool
            - results: Dict[step_id, step_result]
            - context: Dict[variable_name, value]
        """
        pass

    def _build_prompt(self, step: WorkflowStep) -> str:
        """Build prompt for step using context"""
        prompt_parts = [step.task_description]

        # Add input variables from context
        if step.input_variables:
            prompt_parts.append("\n\nContext:")
            for var in step.input_variables:
                if var in self.context:
                    prompt_parts.append(f"\n{var}: {self.context[var]}")

        return "\n".join(prompt_parts)


class DefaultWorkflowExecutor(WorkflowExecutorBase):
    """
    Default workflow executor - simple, transparent execution.
    Supports sequential, parallel, and DAG modes.
    """

    def execute(self) -> Dict[str, Any]:
        """Execute workflow and return results"""
        from agent_builder import AgentBuilder

        builder = AgentBuilder()

        if self.workflow.execution_mode == "sequential":
            return self._execute_sequential(builder)
        elif self.workflow.execution_mode == "parallel":
            return self._execute_parallel(builder)
        elif self.workflow.execution_mode == "dag":
            return self._execute_dag(builder)
        else:
            raise ValueError(f"Unknown execution mode: {self.workflow.execution_mode}")

    def _execute_sequential(self, builder) -> Dict[str, Any]:
        """Execute steps sequentially"""
        from agent_builder import AgentExecutor

        for step in self.workflow.steps:
            print(f"Executing step: {step.name}")

            # Load agent
            agent = builder.load_agent(step.agent_id)
            if not agent:
                self.step_results[step.id] = {
                    "success": False,
                    "error": f"Agent {step.agent_id} not found"
                }
                continue

            # Build prompt with context
            prompt = self._build_prompt(step)

            # Execute agent
            executor = AgentExecutor(agent)
            response = ""
            for chunk in executor.execute(prompt):
                response += chunk

            # Store result
            self.step_results[step.id] = {
                "success": True,
                "output": response
            }

            # Save output variable to context
            if step.output_variable:
                self.context[step.output_variable] = response

        return {
            "success": True,
            "results": self.step_results,
            "context": self.context
        }

    def _execute_parallel(self, builder) -> Dict[str, Any]:
        """Execute steps in parallel (simplified - actually sequential for now)"""
        # TODO: Implement true parallelism with threading or async
        return self._execute_sequential(builder)

    def _execute_dag(self, builder) -> Dict[str, Any]:
        """Execute steps based on dependency graph"""
        # TODO: Implement topological sort and parallel execution
        return self._execute_sequential(builder)


class WorkflowExecutorRegistry:
    """
    Registry for workflow executors.
    Allows plugging in different orchestration engines.

    Usage:
        # Register custom executor
        WorkflowExecutorRegistry.register("crewai", CrewAIExecutor)

        # Use custom executor
        executor = WorkflowExecutorRegistry.get_executor("crewai", workflow)
        result = executor.execute()
    """
    _executors: Dict[str, Type[WorkflowExecutorBase]] = {
        "default": DefaultWorkflowExecutor
    }

    @classmethod
    def register(cls, name: str, executor_class: Type[WorkflowExecutorBase]):
        """Register a new executor"""
        if not issubclass(executor_class, WorkflowExecutorBase):
            raise ValueError(f"{executor_class} must inherit from WorkflowExecutorBase")
        cls._executors[name] = executor_class

    @classmethod
    def get_executor(
        cls,
        name: str,
        workflow: WorkflowConfig
    ) -> WorkflowExecutorBase:
        """Get executor instance by name"""
        if name not in cls._executors:
            raise ValueError(f"Executor '{name}' not registered. Available: {list(cls._executors.keys())}")
        return cls._executors[name](workflow)

    @classmethod
    def list_executors(cls) -> List[str]:
        """List all registered executors"""
        return list(cls._executors.keys())


# Backward compatibility alias
WorkflowExecutor = DefaultWorkflowExecutor


def get_workflow_templates() -> List[Dict[str, Any]]:
    """Get pre-built workflow templates"""
    return [
        {
            "id": "research_analysis",
            "name": "Research & Analysis Pipeline",
            "description": "Research topic → Analyze findings → Generate report",
            "category": "Research",
            "icon": "🔬",
            "steps": [
                {
                    "name": "Research",
                    "task": "Research the given topic and gather information",
                    "output": "research_findings"
                },
                {
                    "name": "Analysis",
                    "task": "Analyze the research findings and identify key insights",
                    "output": "analysis"
                },
                {
                    "name": "Report",
                    "task": "Generate a comprehensive report from the analysis",
                    "output": "final_report"
                }
            ]
        },
        {
            "id": "data_pipeline",
            "name": "Data Analysis Pipeline",
            "description": "Query data → Analyze → Visualize → Report",
            "category": "Data Analysis",
            "icon": "📊",
            "steps": [
                {
                    "name": "Data Extraction",
                    "task": "Extract relevant data using SQL queries",
                    "output": "raw_data"
                },
                {
                    "name": "Data Analysis",
                    "task": "Analyze the data and find patterns",
                    "output": "analysis"
                },
                {
                    "name": "Visualization",
                    "task": "Create visualizations of key findings",
                    "output": "visualizations"
                },
                {
                    "name": "Executive Summary",
                    "task": "Generate executive summary with insights",
                    "output": "summary"
                }
            ]
        },
        {
            "id": "content_creation",
            "name": "Content Creation Workflow",
            "description": "Research → Draft → Review → Publish",
            "category": "Content",
            "icon": "✍️",
            "steps": [
                {
                    "name": "Research",
                    "task": "Research topic and gather sources",
                    "output": "sources"
                },
                {
                    "name": "Draft",
                    "task": "Write initial draft based on research",
                    "output": "draft"
                },
                {
                    "name": "Review",
                    "task": "Review and improve the draft",
                    "output": "reviewed"
                },
                {
                    "name": "Finalize",
                    "task": "Finalize content for publication",
                    "output": "final_content"
                }
            ]
        }
    ]
