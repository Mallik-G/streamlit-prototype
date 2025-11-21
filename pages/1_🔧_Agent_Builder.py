"""
Agent Builder Page - Visual Interface for Creating Custom Agents
Inspired by Databricks Labs Kasal
"""
import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui import load_custom_css, render_header, render_sidebar_section, render_card
from agent_builder import AgentBuilder, AgentTool, AgentConfig, get_available_tools, get_model_options
from agent_templates import get_agent_templates, create_agent_from_template, get_template_categories

# Page configuration
st.set_page_config(
    page_title="Agent Builder - Cortex AI",
    page_icon="🔧",
    layout="wide"
)

# Load custom CSS
load_custom_css()

# Initialize session state
if "current_agent" not in st.session_state:
    st.session_state.current_agent = None
if "builder" not in st.session_state:
    st.session_state.builder = AgentBuilder()
if "agent_name_input" not in st.session_state:
    st.session_state.agent_name_input = ""


render_header("Agent Builder", "Create & Configure Custom AI Agents")

st.markdown("""
<div style="padding: 24px; max-width: 1400px; margin: 0 auto;">
""", unsafe_allow_html=True)

# Tabs for different builder modes
tab1, tab2, tab3 = st.tabs(["📝 Create New Agent", "📚 Templates", "🗂️ My Agents"])

# TAB 1: Create New Agent
with tab1:
    st.markdown("### Configure Your Custom Agent")
    st.markdown("Design an AI agent tailored to your specific needs with custom prompts, models, and tools.")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Basic Information
        st.markdown('<div class="sf-card">', unsafe_allow_html=True)
        st.markdown("#### 📋 Basic Information")

        agent_name = st.text_input(
            "Agent Name",
            placeholder="e.g., Data Analysis Expert",
            key="new_agent_name"
        )

        agent_description = st.text_area(
            "Description",
            placeholder="Describe what this agent does and when to use it...",
            height=80,
            key="new_agent_desc"
        )

        col_cat, col_icon = st.columns([3, 1])
        with col_cat:
            agent_category = st.selectbox(
                "Category",
                options=get_template_categories(),
                key="new_agent_category"
            )

        with col_icon:
            agent_icon = st.text_input(
                "Icon",
                value="🤖",
                max_chars=2,
                key="new_agent_icon"
            )

        agent_tags = st.text_input(
            "Tags (comma-separated)",
            placeholder="e.g., analytics, sql, data",
            key="new_agent_tags"
        )

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Model Configuration
        st.markdown('<div class="sf-card">', unsafe_allow_html=True)
        st.markdown("#### 🤖 Model Configuration")

        model_provider = st.selectbox(
            "Model Provider",
            options=["openai", "anthropic", "databricks"],
            key="new_agent_provider"
        )

        model_options = get_model_options()
        model_name = st.selectbox(
            "Model",
            options=model_options.get(model_provider, []),
            key="new_agent_model"
        )

        col_temp, col_tokens = st.columns(2)
        with col_temp:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Higher values make output more creative",
                key="new_agent_temp"
            )

        with col_tokens:
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=100,
                max_value=4000,
                value=2000,
                step=100,
                key="new_agent_tokens"
            )

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # System Prompt
        st.markdown('<div class="sf-card">', unsafe_allow_html=True)
        st.markdown("#### 💭 System Prompt")
        st.markdown("Define the agent's behavior, expertise, and communication style.")

        system_prompt = st.text_area(
            "System Prompt",
            placeholder="""You are an expert assistant specializing in...

Your capabilities:
- List key capabilities here

Your approach:
- Describe how you work
- Communication style
- Key principles""",
            height=250,
            key="new_agent_prompt",
            label_visibility="collapsed"
        )

        # Prompt templates
        st.markdown("**Quick Prompts:**")
        prompt_cols = st.columns(4)

        with prompt_cols[0]:
            if st.button("📊 Analyst", use_container_width=True):
                st.session_state.new_agent_prompt = "You are a data analyst expert..."
                st.rerun()

        with prompt_cols[1]:
            if st.button("💾 SQL Expert", use_container_width=True):
                st.session_state.new_agent_prompt = "You are a SQL database expert..."
                st.rerun()

        with prompt_cols[2]:
            if st.button("🐍 Developer", use_container_width=True):
                st.session_state.new_agent_prompt = "You are an expert Python developer..."
                st.rerun()

        with prompt_cols[3]:
            if st.button("💬 Support", use_container_width=True):
                st.session_state.new_agent_prompt = "You are a friendly customer support agent..."
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Tools Configuration
        st.markdown('<div class="sf-card">', unsafe_allow_html=True)
        st.markdown("#### 🛠️ Tools & Capabilities")
        st.markdown("Select tools this agent can use")

        available_tools = get_available_tools()
        selected_tools = []

        for tool in available_tools:
            col_check, col_info = st.columns([1, 5])
            with col_check:
                enabled = st.checkbox(
                    "✓",
                    key=f"tool_{tool['id']}",
                    label_visibility="collapsed"
                )
            with col_info:
                st.markdown(f"""
                <div style="margin-bottom: 12px;">
                    <div style="font-weight: 600;">{tool['icon']} {tool['name']}</div>
                    <div style="font-size: 12px; color: var(--sf-text-muted);">{tool['description']}</div>
                </div>
                """, unsafe_allow_html=True)

            if enabled:
                selected_tools.append(tool['id'])

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Memory & Advanced
        st.markdown('<div class="sf-card">', unsafe_allow_html=True)
        st.markdown("#### ⚙️ Advanced Settings")

        enable_memory = st.toggle(
            "Enable Memory",
            value=True,
            help="Agent remembers conversation history",
            key="new_agent_memory"
        )

        if enable_memory:
            memory_type = st.selectbox(
                "Memory Type",
                options=["buffer", "summary", "window"],
                key="new_agent_memory_type"
            )
        else:
            memory_type = "none"

        st.markdown("<br>", unsafe_allow_html=True)

        # RAG / Knowledge Base
        enable_rag = st.toggle(
            "Enable RAG (Retrieval-Augmented Generation)",
            value=False,
            help="Use vector search to retrieve context from documents",
            key="new_agent_rag"
        )

        vector_search_id = None
        if enable_rag:
            from utils.vector_search import VectorSearchManager

            vector_manager = VectorSearchManager()
            indexes = vector_manager.list_configs()

            if indexes:
                index_options = {f"🔍 {idx.name} ({idx.provider})": idx.id for idx in indexes}
                selected_kb = st.selectbox(
                    "Knowledge Base",
                    options=list(index_options.keys()),
                    key="new_agent_kb",
                    help="Select vector search index for RAG"
                )
                vector_search_id = index_options[selected_kb]

                # Automatically add RAG tool if not already selected
                if 'rag_retrieval' not in selected_tools:
                    selected_tools.append('rag_retrieval')

                st.success("✅ RAG enabled with selected knowledge base")
            else:
                st.warning("⚠️ No knowledge bases found. Create one in the Knowledge Base page first.")
                enable_rag = False

        st.markdown("<br>", unsafe_allow_html=True)

        is_public = st.toggle(
            "Make Public",
            value=False,
            help="Share agent in marketplace",
            key="new_agent_public"
        )

        st.markdown('</div>', unsafe_allow_html=True)

    # Create Agent Button
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🚀 Create Agent", type="primary", use_container_width=True):
            if not agent_name:
                st.error("Please provide an agent name")
            elif not system_prompt:
                st.error("Please provide a system prompt")
            else:
                # Create tools list
                tools = [
                    AgentTool(
                        name=tool_id,
                        description=next(t['description'] for t in available_tools if t['id'] == tool_id)
                    )
                    for tool_id in selected_tools
                ]

                # Create agent
                agent = st.session_state.builder.create_agent(
                    name=agent_name,
                    description=agent_description,
                    system_prompt=system_prompt,
                    model_provider=model_provider,
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    enable_memory=enable_memory,
                    memory_type=memory_type,
                    tools=tools,
                    tags=[t.strip() for t in agent_tags.split(",")] if agent_tags else [],
                    category=agent_category,
                    icon=agent_icon,
                    is_public=is_public,
                    vector_search_id=vector_search_id,
                    enable_rag=enable_rag,
                    creator=os.getenv("USER", "anonymous")
                )

                st.success(f"✅ Agent '{agent_name}' created successfully!")
                st.balloons()
                st.session_state.current_agent = agent
                st.rerun()

# TAB 2: Templates
with tab2:
    st.markdown("### Agent Templates")
    st.markdown("Start with pre-configured agents optimized for common use cases")
    st.markdown("<br>", unsafe_allow_html=True)

    # Category filter
    categories = ["All"] + get_template_categories()
    selected_category = st.selectbox("Filter by Category", categories)

    templates = get_agent_templates()
    if selected_category != "All":
        templates = [t for t in templates if t["category"] == selected_category]

    # Display templates in grid
    cols = st.columns(3)
    for idx, template in enumerate(templates):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="sf-card" style="min-height: 200px;">
                <div style="font-size: 36px; margin-bottom: 12px;">{template['icon']}</div>
                <div class="sf-card-title">{template['name']}</div>
                <div class="sf-card-description">{template['description']}</div>
                <div style="margin-top: 12px; font-size: 11px; color: var(--sf-text-muted);">
                    {template['category']} • {template['model_provider']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("👁️ Preview", key=f"preview_{template['id']}", use_container_width=True):
                    with st.expander("Template Details", expanded=True):
                        st.markdown(f"**Model:** {template['model_name']}")
                        st.markdown(f"**Temperature:** {template['temperature']}")
                        st.markdown(f"**Tools:** {', '.join(template['tools'])}")
                        st.markdown("**System Prompt:**")
                        st.text_area("", value=template['system_prompt'], height=200, disabled=True)

            with col2:
                if st.button("📥 Use Template", key=f"use_{template['id']}", use_container_width=True):
                    agent = create_agent_from_template(
                        template['id'],
                        creator=os.getenv("USER", "anonymous")
                    )
                    st.session_state.builder.save_agent(agent)
                    st.success(f"✅ Created '{agent.name}' from template!")
                    st.rerun()

# TAB 3: My Agents
with tab3:
    st.markdown("### My Agents")
    st.markdown("Manage your created agents")
    st.markdown("<br>", unsafe_allow_html=True)

    agents = st.session_state.builder.list_agents()

    if not agents:
        st.info("You haven't created any agents yet. Start by creating a new agent or using a template!")
    else:
        # Display agents
        for agent in agents:
            with st.container():
                st.markdown(f"""
                <div class="sf-card">
                    <div style="display: flex; align-items: center; gap: 16px;">
                        <div style="font-size: 40px;">{agent.icon}</div>
                        <div style="flex: 1;">
                            <div class="sf-card-title">{agent.name}</div>
                            <div class="sf-card-description">{agent.description}</div>
                            <div style="margin-top: 8px; font-size: 11px; color: var(--sf-text-muted);">
                                {agent.category} • {agent.model_name} •
                                {"🌐 Public" if agent.is_public else "🔒 Private"}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button("💬 Chat", key=f"chat_{agent.id}", use_container_width=True):
                        st.session_state.selected_agent_id = agent.id
                        st.switch_page("app.py")

                with col2:
                    if st.button("📝 Edit", key=f"edit_{agent.id}", use_container_width=True):
                        st.info("Edit functionality coming soon!")

                with col3:
                    publish_label = "🔒 Unpublish" if agent.is_public else "🌐 Publish"
                    if st.button(publish_label, key=f"publish_{agent.id}", use_container_width=True):
                        if agent.is_public:
                            st.session_state.builder.unpublish_agent(agent.id)
                            st.success("Agent unpublished")
                        else:
                            st.session_state.builder.publish_agent(agent.id)
                            st.success("Agent published to marketplace!")
                        st.rerun()

                with col4:
                    if st.button("🗑️ Delete", key=f"delete_{agent.id}", use_container_width=True):
                        st.session_state.builder.delete_agent(agent.id)
                        st.success("Agent deleted")
                        st.rerun()

                st.markdown("<br>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
