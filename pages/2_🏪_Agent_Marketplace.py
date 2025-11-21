"""
Agent Marketplace - Discover and Deploy Agents from Community
"""
import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui import load_custom_css, render_header
from agent_builder import AgentBuilder
from agent_templates import get_template_categories

# Page configuration
st.set_page_config(
    page_title="Agent Marketplace - Cortex AI",
    page_icon="🏪",
    layout="wide"
)

# Load custom CSS
load_custom_css()

# Initialize session state
if "builder" not in st.session_state:
    st.session_state.builder = AgentBuilder()

render_header("Agent Marketplace", "Discover & Deploy Community Agents")

st.markdown("""
<div style="padding: 24px; max-width: 1400px; margin: 0 auto;">
""", unsafe_allow_html=True)

# Search and Filter Bar
st.markdown('<div class="sf-card">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_query = st.text_input(
        "Search agents",
        placeholder="Search by name, description, or tags...",
        label_visibility="collapsed"
    )

with col2:
    category_filter = st.selectbox(
        "Category",
        options=["All Categories"] + get_template_categories(),
        label_visibility="collapsed"
    )

with col3:
    sort_by = st.selectbox(
        "Sort by",
        options=["Recently Updated", "Most Popular", "Name"],
        label_visibility="collapsed"
    )

st.markdown('</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Get public agents
public_agents = st.session_state.builder.list_agents(public_only=True)

# Apply filters
if category_filter != "All Categories":
    public_agents = [a for a in public_agents if a.category == category_filter]

if search_query:
    search_lower = search_query.lower()
    public_agents = [
        a for a in public_agents
        if search_lower in a.name.lower()
        or search_lower in a.description.lower()
        or any(search_lower in tag.lower() for tag in a.tags)
    ]

# Display stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="sf-card" style="text-align: center;">
        <div style="font-size: 32px; font-weight: 700; color: var(--sf-primary);">{len(public_agents)}</div>
        <div style="font-size: 12px; color: var(--sf-text-muted); text-transform: uppercase;">Available Agents</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    categories_count = len(set(a.category for a in public_agents))
    st.markdown(f"""
    <div class="sf-card" style="text-align: center;">
        <div style="font-size: 32px; font-weight: 700; color: var(--sf-secondary);">{categories_count}</div>
        <div style="font-size: 12px; color: var(--sf-text-muted); text-transform: uppercase;">Categories</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    creators_count = len(set(a.creator for a in public_agents))
    st.markdown(f"""
    <div class="sf-card" style="text-align: center;">
        <div style="font-size: 32px; font-weight: 700; color: var(--sf-success);">{creators_count}</div>
        <div style="font-size: 12px; color: var(--sf-text-muted); text-transform: uppercase;">Contributors</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="sf-card" style="text-align: center;">
        <div style="font-size: 32px; font-weight: 700; color: var(--sf-warning);">⭐</div>
        <div style="font-size: 12px; color: var(--sf-text-muted); text-transform: uppercase;">Featured</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Display agents
if not public_agents:
    st.info("No agents found matching your criteria. Try adjusting your filters or be the first to publish an agent!")
else:
    st.markdown(f"### Showing {len(public_agents)} agents")
    st.markdown("<br>", unsafe_allow_html=True)

    # Grid layout - 2 columns
    cols = st.columns(2)

    for idx, agent in enumerate(public_agents):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="sf-card" style="height: 100%;">
                <div style="display: flex; gap: 16px;">
                    <div style="font-size: 48px; flex-shrink: 0;">{agent.icon}</div>
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: start; justify-content: space-between;">
                            <div class="sf-card-title">{agent.name}</div>
                            <div class="sf-status-badge sf-status-success">
                                <span>●</span> Active
                            </div>
                        </div>
                        <div class="sf-card-description" style="margin-top: 8px; margin-bottom: 12px;">
                            {agent.description}
                        </div>
                        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px;">
                            {' '.join([f'<span style="background: var(--sf-primary-light); color: var(--sf-primary-dark); padding: 4px 8px; border-radius: 4px; font-size: 11px;">#{tag}</span>' for tag in agent.tags[:3]])}
                        </div>
                        <div style="font-size: 11px; color: var(--sf-text-muted); margin-bottom: 12px;">
                            📂 {agent.category} • 🤖 {agent.model_name} • 👤 {agent.creator}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("👁️ Details", key=f"details_{agent.id}_{idx}", use_container_width=True):
                    st.session_state[f"show_details_{agent.id}"] = not st.session_state.get(f"show_details_{agent.id}", False)
                    st.rerun()

            with col2:
                if st.button("💬 Try Now", key=f"try_{agent.id}_{idx}", use_container_width=True, type="primary"):
                    st.session_state.selected_agent_id = agent.id
                    st.switch_page("app.py")

            with col3:
                if st.button("📥 Clone", key=f"clone_{agent.id}_{idx}", use_container_width=True):
                    cloned = st.session_state.builder.duplicate_agent(
                        agent.id,
                        new_name=f"{agent.name} (Copy)",
                        creator=os.getenv("USER", "anonymous")
                    )
                    if cloned:
                        st.success(f"✅ Cloned '{agent.name}' to your agents!")
                        st.rerun()

            # Show details if expanded
            if st.session_state.get(f"show_details_{agent.id}", False):
                with st.expander("Agent Details", expanded=True):
                    tab1, tab2, tab3 = st.tabs(["Overview", "System Prompt", "Configuration"])

                    with tab1:
                        st.markdown(f"**Description:** {agent.description}")
                        st.markdown(f"**Category:** {agent.category}")
                        st.markdown(f"**Version:** {agent.version}")
                        st.markdown(f"**Created:** {agent.created_at[:10]}")
                        st.markdown(f"**Last Updated:** {agent.updated_at[:10]}")
                        st.markdown(f"**Tags:** {', '.join(agent.tags)}")

                        if agent.tools:
                            st.markdown("**Tools:**")
                            for tool in agent.tools:
                                st.markdown(f"- {tool.name}")

                    with tab2:
                        st.text_area(
                            "System Prompt",
                            value=agent.system_prompt,
                            height=300,
                            disabled=True,
                            label_visibility="collapsed"
                        )

                    with tab3:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Provider:** {agent.model_provider}")
                            st.markdown(f"**Model:** {agent.model_name}")
                            st.markdown(f"**Temperature:** {agent.temperature}")
                        with col2:
                            st.markdown(f"**Max Tokens:** {agent.max_tokens}")
                            st.markdown(f"**Memory:** {'Enabled' if agent.enable_memory else 'Disabled'}")
                            st.markdown(f"**Memory Type:** {agent.memory_type}")

            st.markdown("<br>", unsafe_allow_html=True)

# Sidebar - Featured Categories
with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 0; border-bottom: 1px solid var(--sf-border); margin-bottom: 20px;">
        <div style="font-weight: 600; font-size: 16px;">Agent Marketplace</div>
        <div style="font-size: 12px; color: var(--sf-text-muted);">Discover & Deploy</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 Popular Categories")
    categories = get_template_categories()

    for category in categories:
        count = len([a for a in public_agents if a.category == category])
        if st.button(f"{category} ({count})", use_container_width=True, key=f"cat_{category}"):
            st.session_state.category_filter = category
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🏆 Top Contributors")

    # Count agents by creator
    from collections import Counter
    creator_counts = Counter(a.creator for a in public_agents)
    top_creators = creator_counts.most_common(5)

    for creator, count in top_creators:
        st.markdown(f"""
        <div style="padding: 8px; border-bottom: 1px solid var(--sf-border-light);">
            <div style="font-weight: 500;">{creator}</div>
            <div style="font-size: 11px; color: var(--sf-text-muted);">{count} agents published</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 💡 Getting Started")
    st.markdown("""
    1. **Browse** agents by category
    2. **Try** agents directly in chat
    3. **Clone** agents to customize
    4. **Publish** your own agents
    """)

st.markdown("</div>", unsafe_allow_html=True)
