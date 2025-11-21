"""
Workflow Builder - Multi-Agent Workflow Orchestration
Create, visualize, and execute multi-step agent workflows
"""
import streamlit as st
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui import load_custom_css, render_header
from config import get_platform_config
from workflow_builder import (
    WorkflowBuilder,
    WorkflowExecutor,
    WorkflowStep,
    WorkflowConfig,
    get_workflow_templates
)
from agent_builder import AgentBuilder
import uuid

# Page configuration
st.set_page_config(
    page_title="Workflow Builder - Cortex AI",
    page_icon="📊",
    layout="wide"
)

# Load custom CSS
load_custom_css()

# Initialize
platform_config = get_platform_config()
workflow_builder = WorkflowBuilder()
agent_builder = AgentBuilder()

# Initialize session state
if 'workflow_steps' not in st.session_state:
    st.session_state.workflow_steps = []
if 'editing_workflow_id' not in st.session_state:
    st.session_state.editing_workflow_id = None

render_header("Workflow Builder", "Multi-Agent Orchestration")

st.markdown("""
<div style="padding: 24px; max-width: 1400px; margin: 0 auto;">
""", unsafe_allow_html=True)

# Info banner
st.markdown("""
<div style="background: var(--sf-primary-light); border: 1px solid var(--sf-primary);
            border-radius: 8px; padding: 16px; margin-bottom: 24px;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 36px;">🔄</span>
        <div style="flex: 1;">
            <div style="font-weight: 600; font-size: 16px;">Multi-Agent Workflows</div>
            <div style="font-size: 13px; color: var(--sf-text-muted); margin-top: 4px;">
                Chain multiple agents together for complex tasks. Configure workflows via forms,
                stored as YAML, visualized with Mermaid diagrams.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Create Workflow",
    "👁️ Preview & Execute",
    "📋 Templates",
    "📂 My Workflows"
])

# TAB 1: CREATE WORKFLOW
with tab1:
    st.markdown("### Workflow Configuration")

    col1, col2 = st.columns([2, 1])

    with col1:
        workflow_name = st.text_input(
            "Workflow Name",
            value="",
            placeholder="e.g., Data Analysis Pipeline",
            key="wf_name"
        )

        workflow_description = st.text_area(
            "Description",
            placeholder="Describe what this workflow does...",
            height=80,
            key="wf_desc"
        )

    with col2:
        execution_mode = st.selectbox(
            "Execution Mode",
            options=["sequential", "parallel", "dag"],
            help="Sequential: Steps run one after another\nParallel: All steps run simultaneously\nDAG: Steps run based on dependencies"
        )

        category = st.selectbox(
            "Category",
            options=["Data Analysis", "Research", "Content", "Development", "Support", "General"]
        )

        is_public = st.checkbox("Share in marketplace", value=False)

    st.markdown("---")
    st.markdown("### Workflow Steps")

    # Get available agents
    agents = agent_builder.list_agents()
    agent_options = {f"{a.name} ({a.id[:8]})": a.id for a in agents}

    if not agents:
        st.warning("⚠️ No agents found. Create agents first in the Agent Builder.")
    else:
        # Add step form
        with st.expander("➕ Add New Step", expanded=len(st.session_state.workflow_steps) == 0):
            col1, col2 = st.columns(2)

            with col1:
                step_name = st.text_input("Step Name", placeholder="e.g., Research Topic", key="step_name")
                selected_agent = st.selectbox("Agent", options=list(agent_options.keys()), key="step_agent")
                task_description = st.text_area(
                    "Task Description",
                    placeholder="What should this agent do?",
                    height=100,
                    key="step_task"
                )

            with col2:
                input_variables = st.text_area(
                    "Input Variables (one per line)",
                    placeholder="user_query\nprevious_results",
                    help="Variables this step needs from previous steps",
                    key="step_inputs"
                )

                output_variable = st.text_input(
                    "Output Variable Name",
                    placeholder="e.g., research_findings",
                    help="Name for this step's output to be used by later steps",
                    key="step_output"
                )

                timeout = st.number_input("Timeout (seconds)", min_value=30, max_value=3600, value=300, key="step_timeout")
                retry = st.number_input("Retry Count", min_value=0, max_value=5, value=0, key="step_retry")

            # Platform tools selection
            st.markdown("**Platform Tools** (optional)")
            platform_tools_input = st.text_input(
                "Platform Tools (comma-separated)",
                placeholder="e.g., calculate_revenue, sentiment_analysis",
                help="Functions registered in Unity Catalog or Snowflake UDFs",
                key="step_tools"
            )

            # Dependencies (for DAG mode)
            if execution_mode == "dag":
                st.markdown("**Dependencies**")
                existing_step_ids = [s["id"] for s in st.session_state.workflow_steps]
                depends_on = st.multiselect(
                    "Depends on steps",
                    options=existing_step_ids,
                    help="Which steps must complete before this one",
                    key="step_depends"
                )
            else:
                depends_on = []

            if st.button("➕ Add Step", type="primary", use_container_width=True):
                if step_name and task_description and selected_agent:
                    # Parse inputs
                    input_vars = [v.strip() for v in input_variables.split('\n') if v.strip()]
                    platform_tools = [t.strip() for t in platform_tools_input.split(',') if t.strip()]

                    new_step = {
                        "id": str(uuid.uuid4()),
                        "name": step_name,
                        "agent_id": agent_options[selected_agent],
                        "task_description": task_description,
                        "input_variables": input_vars,
                        "output_variable": output_variable,
                        "platform_tools": platform_tools,
                        "depends_on": depends_on,
                        "timeout": timeout,
                        "retry": retry
                    }

                    st.session_state.workflow_steps.append(new_step)
                    st.success(f"✅ Added step: {step_name}")
                    st.rerun()
                else:
                    st.error("Please fill in required fields: Step Name, Task Description, and Agent")

        # Display existing steps
        if st.session_state.workflow_steps:
            st.markdown(f"**Current Steps** ({len(st.session_state.workflow_steps)})")

            for idx, step in enumerate(st.session_state.workflow_steps):
                with st.container():
                    st.markdown(f"""
                    <div class="sf-card" style="margin-bottom: 12px;">
                        <div style="display: flex; align-items: start; gap: 12px;">
                            <div style="font-size: 28px; font-weight: 600; color: var(--sf-primary);">{idx + 1}</div>
                            <div style="flex: 1;">
                                <div class="sf-card-title">{step['name']}</div>
                                <div class="sf-card-description">{step['task_description'][:100]}...</div>
                                <div style="margin-top: 8px; font-size: 11px; color: var(--sf-text-muted);">
                                    <strong>Output:</strong> {step['output_variable'] or 'None'} |
                                    <strong>Timeout:</strong> {step['timeout']}s
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
                    with col1:
                        if idx > 0:
                            if st.button("⬆️", key=f"up_{idx}", help="Move up"):
                                st.session_state.workflow_steps[idx], st.session_state.workflow_steps[idx-1] = \
                                    st.session_state.workflow_steps[idx-1], st.session_state.workflow_steps[idx]
                                st.rerun()
                    with col2:
                        if idx < len(st.session_state.workflow_steps) - 1:
                            if st.button("⬇️", key=f"down_{idx}", help="Move down"):
                                st.session_state.workflow_steps[idx], st.session_state.workflow_steps[idx+1] = \
                                    st.session_state.workflow_steps[idx+1], st.session_state.workflow_steps[idx]
                                st.rerun()
                    with col3:
                        if st.button("🗑️", key=f"del_{idx}", help="Delete"):
                            st.session_state.workflow_steps.pop(idx)
                            st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            # Save workflow
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("💾 Save Workflow", type="primary", use_container_width=True):
                    if workflow_name and workflow_description and st.session_state.workflow_steps:
                        # Create workflow steps
                        steps = [
                            WorkflowStep(**step) for step in st.session_state.workflow_steps
                        ]

                        # Create workflow
                        workflow = workflow_builder.create_workflow(
                            name=workflow_name,
                            description=workflow_description,
                            steps=steps,
                            execution_mode=execution_mode,
                            creator="current_user",
                            tags=[category.lower()],
                            category=category,
                            is_public=is_public
                        )

                        st.success(f"✅ Workflow '{workflow_name}' saved successfully!")
                        st.session_state.workflow_steps = []
                        st.session_state.editing_workflow_id = workflow.id
                        st.rerun()
                    else:
                        st.error("Please provide workflow name, description, and at least one step")
        else:
            st.info("👆 Add steps to your workflow using the form above")

# TAB 2: PREVIEW & EXECUTE
with tab2:
    st.markdown("### Workflow Preview")

    if st.session_state.workflow_steps:
        # Create temporary workflow for preview
        steps = [WorkflowStep(**step) for step in st.session_state.workflow_steps]
        temp_workflow = WorkflowConfig(
            id="preview",
            name=workflow_name or "Untitled Workflow",
            description=workflow_description or "No description",
            creator="current_user",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            steps=steps,
            execution_mode=execution_mode,
            tags=[],
            category="general"
        )

        # Display Mermaid diagram
        st.markdown("#### Workflow Diagram")
        mermaid_code = temp_workflow.to_mermaid()

        st.code(mermaid_code, language="mermaid")

        # Display YAML
        st.markdown("#### YAML Configuration")
        with st.expander("View YAML"):
            st.code(temp_workflow.to_yaml(), language="yaml")

        # Execute workflow
        st.markdown("---")
        st.markdown("#### Execute Workflow")

        initial_context = st.text_area(
            "Initial Context (JSON format)",
            placeholder='{"user_query": "Analyze Q4 sales data"}',
            help="Provide initial variables for the workflow"
        )

        if st.button("▶️ Execute Workflow", type="primary"):
            with st.spinner("Executing workflow..."):
                try:
                    # Parse initial context
                    import json
                    if initial_context:
                        context = json.loads(initial_context)
                        temp_workflow.context = context

                    # Create executor
                    executor = WorkflowExecutor(temp_workflow)

                    # Execute
                    result = executor.execute()

                    if result.get('success'):
                        st.success("✅ Workflow executed successfully!")

                        # Display results
                        st.markdown("#### Execution Results")
                        for step_id, step_result in result['results'].items():
                            step = next((s for s in temp_workflow.steps if s.id == step_id), None)
                            if step:
                                with st.expander(f"📋 {step.name}"):
                                    if step_result.get('success'):
                                        st.markdown("**Status:** ✅ Success")
                                        st.markdown("**Output:**")
                                        st.text(step_result.get('output', 'No output'))
                                    else:
                                        st.markdown("**Status:** ❌ Failed")
                                        st.error(step_result.get('error', 'Unknown error'))

                        # Display final context
                        st.markdown("#### Final Context")
                        st.json(result.get('context', {}))
                    else:
                        st.error("❌ Workflow execution failed")

                except Exception as e:
                    st.error(f"Error executing workflow: {str(e)}")
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())

    elif st.session_state.editing_workflow_id:
        # Load and preview saved workflow
        workflow = workflow_builder.load_workflow(st.session_state.editing_workflow_id)
        if workflow:
            st.markdown(f"### {workflow.name}")
            st.markdown(workflow.description)

            st.markdown("#### Workflow Diagram")
            st.code(workflow.to_mermaid(), language="mermaid")

            with st.expander("View YAML"):
                st.code(workflow.to_yaml(), language="yaml")
    else:
        st.info("👈 Create a workflow in the 'Create Workflow' tab to preview it here")

# TAB 3: TEMPLATES
with tab3:
    st.markdown("### Workflow Templates")
    st.markdown("Start with a pre-built workflow template and customize it to your needs.")

    templates = get_workflow_templates()

    for template in templates:
        st.markdown(f"""
        <div class="sf-card">
            <div style="display: flex; align-items: start; gap: 12px;">
                <div style="font-size: 36px;">{template['icon']}</div>
                <div style="flex: 1;">
                    <div class="sf-card-title">{template['name']}</div>
                    <div class="sf-card-description">{template['description']}</div>
                    <div style="margin-top: 12px; font-size: 11px; color: var(--sf-text-muted);">
                        <strong>Category:</strong> {template['category']} |
                        <strong>Steps:</strong> {len(template['steps'])}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])

        with col1:
            with st.expander(f"📋 View Template Steps"):
                for idx, step in enumerate(template['steps']):
                    st.markdown(f"""
                    **Step {idx + 1}: {step['name']}**
                    - Task: {step['task']}
                    - Output: `{step['output']}`
                    """)

        with col2:
            if st.button(f"Use Template", key=f"use_{template['id']}", use_container_width=True):
                # Clear existing steps and populate with template
                st.session_state.workflow_steps = []

                for step in template['steps']:
                    # Need to assign agents - use first available agent as placeholder
                    agent_id = agents[0].id if agents else ""

                    new_step = {
                        "id": str(uuid.uuid4()),
                        "name": step['name'],
                        "agent_id": agent_id,
                        "task_description": step['task'],
                        "input_variables": [],
                        "output_variable": step['output'],
                        "platform_tools": [],
                        "depends_on": [],
                        "timeout": 300,
                        "retry": 0
                    }
                    st.session_state.workflow_steps.append(new_step)

                st.success(f"✅ Template loaded! Go to 'Create Workflow' tab to customize and save.")
                st.info("⚠️ Don't forget to assign appropriate agents to each step!")

        st.markdown("<br>", unsafe_allow_html=True)

# TAB 4: MY WORKFLOWS
with tab4:
    st.markdown("### My Workflows")

    # Filter options
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        filter_category = st.selectbox(
            "Filter by Category",
            options=["All", "Data Analysis", "Research", "Content", "Development", "Support", "General"]
        )
    with col2:
        search_query = st.text_input("Search", placeholder="Search workflows...")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        show_public_only = st.checkbox("Public only")

    # Load workflows
    workflows = workflow_builder.list_workflows(
        category=None if filter_category == "All" else filter_category,
        public_only=show_public_only
    )

    # Apply search filter
    if search_query:
        workflows = [w for w in workflows if search_query.lower() in w.name.lower() or search_query.lower() in w.description.lower()]

    if not workflows:
        st.info("No workflows found. Create your first workflow in the 'Create Workflow' tab!")
    else:
        st.markdown(f"**Found {len(workflows)} workflow(s)**")

        for workflow in workflows:
            st.markdown(f"""
            <div class="sf-card">
                <div style="display: flex; align-items: start; gap: 12px;">
                    <div style="font-size: 36px;">🔄</div>
                    <div style="flex: 1;">
                        <div class="sf-card-title">{workflow.name}</div>
                        <div class="sf-card-description">{workflow.description}</div>
                        <div style="margin-top: 8px; font-size: 11px; color: var(--sf-text-muted);">
                            <strong>Steps:</strong> {len(workflow.steps)} |
                            <strong>Mode:</strong> {workflow.execution_mode} |
                            <strong>Category:</strong> {workflow.category} |
                            <strong>Updated:</strong> {workflow.updated_at[:10]}
                            {' | 🌐 Public' if workflow.is_public else ''}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                if st.button("👁️ View", key=f"view_{workflow.id}"):
                    st.session_state.editing_workflow_id = workflow.id
                    st.info("Switch to 'Preview & Execute' tab to view the workflow")

            with col2:
                if st.button("▶️ Execute", key=f"exec_{workflow.id}"):
                    st.session_state.editing_workflow_id = workflow.id
                    # Convert to steps format for execution
                    st.session_state.workflow_steps = [
                        {
                            "id": step.id,
                            "name": step.name,
                            "agent_id": step.agent_id,
                            "task_description": step.task_description,
                            "input_variables": step.input_variables,
                            "output_variable": step.output_variable,
                            "platform_tools": step.platform_tools,
                            "depends_on": step.depends_on,
                            "timeout": step.timeout,
                            "retry": step.retry
                        }
                        for step in workflow.steps
                    ]
                    st.info("Switch to 'Preview & Execute' tab to run the workflow")

            with col3:
                # Export options
                export_format = st.selectbox(
                    "Export",
                    options=["YAML", "JSON", "Mermaid"],
                    key=f"export_format_{workflow.id}",
                    label_visibility="collapsed"
                )
                if st.button("📥", key=f"export_{workflow.id}", help="Export workflow"):
                    content = workflow_builder.export_workflow(
                        workflow.id,
                        format=export_format.lower()
                    )
                    if content:
                        st.download_button(
                            label=f"Download {export_format}",
                            data=content,
                            file_name=f"{workflow.name.replace(' ', '_')}.{export_format.lower()}",
                            mime="text/plain",
                            key=f"download_{workflow.id}"
                        )

            with col4:
                if st.button("✏️ Edit", key=f"edit_{workflow.id}"):
                    # Load workflow into editor
                    st.session_state.workflow_steps = [
                        {
                            "id": step.id,
                            "name": step.name,
                            "agent_id": step.agent_id,
                            "task_description": step.task_description,
                            "input_variables": step.input_variables,
                            "output_variable": step.output_variable,
                            "platform_tools": step.platform_tools,
                            "depends_on": step.depends_on,
                            "timeout": step.timeout,
                            "retry": step.retry
                        }
                        for step in workflow.steps
                    ]
                    st.session_state.editing_workflow_id = workflow.id
                    st.info("Switch to 'Create Workflow' tab to edit")

            with col5:
                if st.button("🗑️ Delete", key=f"delete_{workflow.id}"):
                    if workflow_builder.delete_workflow(workflow.id):
                        st.success(f"Deleted workflow: {workflow.name}")
                        st.rerun()
                    else:
                        st.error("Failed to delete workflow")

            st.markdown("<br>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 0; border-bottom: 1px solid var(--sf-border); margin-bottom: 20px;">
        <div style="font-weight: 600; font-size: 16px;">Workflow Builder</div>
        <div style="font-size: 12px; color: var(--sf-text-muted);">Multi-Agent Orchestration</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎯 Execution Modes")
    st.markdown("""
    **Sequential**
    - Steps run one after another
    - Output of step N feeds into step N+1
    - Best for linear pipelines

    **Parallel**
    - All steps run simultaneously
    - No dependencies between steps
    - Fastest for independent tasks

    **DAG (Directed Acyclic Graph)**
    - Steps run based on dependencies
    - Maximum parallelism with constraints
    - Best for complex workflows
    """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 💡 Use Cases")
    st.markdown("""
    - **Research Pipeline**: Research → Analyze → Report
    - **Data Analysis**: Extract → Clean → Visualize → Insights
    - **Content Creation**: Research → Draft → Review → Publish
    - **Customer Support**: Classify → Route → Respond → Follow-up
    """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📚 Resources")
    st.markdown("""
    - [YAML Syntax Guide](https://yaml.org)
    - [Mermaid Diagrams](https://mermaid.js.org)
    - [Best Practices](https://docs.example.com)
    """)

st.markdown("</div>", unsafe_allow_html=True)
