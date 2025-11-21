"""
Unit tests for workflow_builder module
"""
import pytest
from workflow_builder import (
    WorkflowStep,
    WorkflowConfig,
    WorkflowBuilder,
    DefaultWorkflowExecutor,
    WorkflowExecutorRegistry,
)


@pytest.mark.unit
class TestWorkflowStep:
    """Test WorkflowStep dataclass"""

    def test_create_workflow_step(self):
        """Test creating a workflow step"""
        step = WorkflowStep(
            id="step-1",
            name="Test Step",
            agent_id="agent-123",
            task_description="Perform a test task",
            output_variable="result",
        )

        assert step.id == "step-1"
        assert step.name == "Test Step"
        assert step.agent_id == "agent-123"
        assert step.output_variable == "result"
        assert step.input_variables == []
        assert step.timeout == 300


@pytest.mark.unit
class TestWorkflowConfig:
    """Test WorkflowConfig dataclass"""

    def test_create_workflow_config(self):
        """Test creating a workflow configuration"""
        steps = [
            WorkflowStep(
                id="step-1",
                name="Step 1",
                agent_id="agent-1",
                task_description="First step",
                output_variable="output1",
            )
        ]

        workflow = WorkflowConfig(
            id="workflow-1",
            name="Test Workflow",
            description="A test workflow",
            creator="test_user",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            steps=steps,
            execution_mode="sequential",
        )

        assert workflow.id == "workflow-1"
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 1
        assert workflow.execution_mode == "sequential"

    def test_workflow_to_yaml(self):
        """Test converting workflow to YAML"""
        steps = [
            WorkflowStep(
                id="step-1",
                name="Step 1",
                agent_id="agent-1",
                task_description="First step",
            )
        ]

        workflow = WorkflowConfig(
            id="workflow-1",
            name="Test Workflow",
            description="A test workflow",
            creator="test_user",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            steps=steps,
        )

        yaml_str = workflow.to_yaml()
        assert "workflow-1" in yaml_str
        assert "Test Workflow" in yaml_str
        assert "step-1" in yaml_str

    def test_workflow_from_yaml(self):
        """Test creating workflow from YAML"""
        yaml_str = """
id: workflow-1
name: Test Workflow
description: A test workflow
creator: test_user
created_at: '2024-01-01T00:00:00'
updated_at: '2024-01-01T00:00:00'
execution_mode: sequential
steps:
  - id: step-1
    name: Step 1
    agent_id: agent-1
    task_description: First step
    input_variables: []
    output_variable: ''
    platform_tools: []
    depends_on: []
    timeout: 300
    retry: 0
tags: []
is_public: false
category: general
version: 1.0.0
"""
        workflow = WorkflowConfig.from_yaml(yaml_str)
        assert workflow.id == "workflow-1"
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 1

    def test_workflow_to_mermaid(self):
        """Test generating Mermaid diagram"""
        steps = [
            WorkflowStep(
                id="step-1",
                name="Step 1",
                agent_id="agent-1",
                task_description="First step",
                output_variable="output1",
            ),
            WorkflowStep(
                id="step-2",
                name="Step 2",
                agent_id="agent-2",
                task_description="Second step",
                input_variables=["output1"],
            ),
        ]

        workflow = WorkflowConfig(
            id="workflow-1",
            name="Test Workflow",
            description="A test workflow",
            creator="test_user",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            steps=steps,
            execution_mode="sequential",
        )

        mermaid = workflow.to_mermaid()
        assert "graph TD" in mermaid
        assert "step_1" in mermaid
        assert "step_2" in mermaid


@pytest.mark.unit
class TestWorkflowBuilder:
    """Test WorkflowBuilder class"""

    def test_create_workflow(self, tmp_path):
        """Test creating a workflow"""
        builder = WorkflowBuilder(storage_path=str(tmp_path))

        steps = [
            WorkflowStep(
                id="step-1",
                name="Step 1",
                agent_id="agent-1",
                task_description="First step",
            )
        ]

        workflow = builder.create_workflow(
            name="Test Workflow",
            description="A test workflow",
            steps=steps,
        )

        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 1

        # Check that file was created
        yaml_file = tmp_path / f"{workflow.id}.yaml"
        assert yaml_file.exists()

    def test_load_workflow(self, tmp_path):
        """Test loading a workflow"""
        builder = WorkflowBuilder(storage_path=str(tmp_path))

        # Create workflow
        steps = [
            WorkflowStep(
                id="step-1",
                name="Step 1",
                agent_id="agent-1",
                task_description="First step",
            )
        ]

        created_workflow = builder.create_workflow(
            name="Test Workflow",
            description="A test workflow",
            steps=steps,
        )

        # Load workflow
        loaded_workflow = builder.load_workflow(created_workflow.id)

        assert loaded_workflow is not None
        assert loaded_workflow.id == created_workflow.id
        assert loaded_workflow.name == "Test Workflow"

    def test_list_workflows(self, tmp_path):
        """Test listing workflows"""
        builder = WorkflowBuilder(storage_path=str(tmp_path))

        # Create multiple workflows
        for i in range(3):
            steps = [
                WorkflowStep(
                    id=f"step-{i}",
                    name=f"Step {i}",
                    agent_id=f"agent-{i}",
                    task_description=f"Step {i}",
                )
            ]

            builder.create_workflow(
                name=f"Workflow {i}",
                description=f"Description {i}",
                steps=steps,
            )

        workflows = builder.list_workflows()
        assert len(workflows) == 3


@pytest.mark.unit
class TestWorkflowExecutorRegistry:
    """Test WorkflowExecutorRegistry"""

    def test_list_executors(self):
        """Test listing registered executors"""
        executors = WorkflowExecutorRegistry.list_executors()
        assert "default" in executors

    def test_get_default_executor(self):
        """Test getting default executor"""
        steps = [
            WorkflowStep(
                id="step-1",
                name="Step 1",
                agent_id="agent-1",
                task_description="First step",
            )
        ]

        workflow = WorkflowConfig(
            id="workflow-1",
            name="Test Workflow",
            description="A test workflow",
            creator="test_user",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            steps=steps,
        )

        executor = WorkflowExecutorRegistry.get_executor("default", workflow)
        assert isinstance(executor, DefaultWorkflowExecutor)

    def test_register_custom_executor(self):
        """Test registering a custom executor"""
        from workflow_builder import WorkflowExecutorBase

        class CustomExecutor(WorkflowExecutorBase):
            def execute(self):
                return {"success": True, "results": {}, "context": {}}

        WorkflowExecutorRegistry.register("custom", CustomExecutor)

        executors = WorkflowExecutorRegistry.list_executors()
        assert "custom" in executors


@pytest.mark.integration
class TestWorkflowExecution:
    """Integration tests for workflow execution"""

    @pytest.mark.skip(reason="Requires agent setup")
    def test_execute_sequential_workflow(self):
        """Test executing a sequential workflow"""
        # This would require actual agents to be set up
        # Skip for now, implement when agent mocking is available
        pass
