"""
Domain-Based Agent Setup

Quick setup for domain-specific agents using auto-discovery.
Discovers tables, metrics, and functions tagged with domain in Unity Catalog/Snowflake.
"""
import streamlit as st
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui import load_custom_css, render_header
from config import get_platform_config
from utils.domain_discovery import DomainDiscoveryEngine, DomainProfile
from agent_builder import AgentBuilder
import json

# Page configuration
st.set_page_config(
    page_title="Domain Setup - Cortex AI",
    page_icon="🎯",
    layout="wide"
)

# Load custom CSS
load_custom_css()

# Initialize
platform_config = get_platform_config()
discovery_engine = DomainDiscoveryEngine(platform_config)
agent_builder = AgentBuilder()

# Initialize session state
if 'discovered_profile' not in st.session_state:
    st.session_state.discovered_profile = None
if 'discovery_in_progress' not in st.session_state:
    st.session_state.discovery_in_progress = False

render_header("Domain-Based Agent Setup", "Auto-discover resources and create specialized agents")

st.markdown("""
<div style="padding: 24px; max-width: 1400px; margin: 0 auto;">
""", unsafe_allow_html=True)

# Info banner
st.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px; padding: 24px; margin-bottom: 32px; color: white;">
    <div style="display: flex; align-items: center; gap: 16px;">
        <span style="font-size: 48px;">🎯</span>
        <div style="flex: 1;">
            <div style="font-weight: 700; font-size: 24px; margin-bottom: 8px;">
                Intelligent Domain Discovery
            </div>
            <div style="font-size: 14px; opacity: 0.95;">
                Say: <strong>"I want to be a Finance Analyst in Finance BU"</strong><br>
                We'll automatically discover all finance tables, metrics, and functions from your catalog,
                then configure a specialized agent with the right context and tools.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Main tabs
tab1, tab2, tab3 = st.tabs([
    "🔍 Discover Domain",
    "🤖 Create Agent",
    "📊 Discovered Resources"
])

# TAB 1: DISCOVER DOMAIN
with tab1:
    st.markdown("### Select Your Domain")

    col1, col2 = st.columns([2, 1])

    with col1:
        # List available domains
        available_domains = discovery_engine.list_available_domains()

        st.markdown("#### Available Domains")
        domain_names = [d["name"] for d in available_domains]

        selected_domain = st.selectbox(
            "Domain",
            options=domain_names,
            help="Domains are discovered from catalog tags"
        )

        # Show domain description
        domain_desc = next(
            (d["description"] for d in available_domains if d["name"] == selected_domain),
            ""
        )
        if domain_desc:
            st.caption(f"ℹ️ {domain_desc}")

        # Optional: Business unit filter
        business_unit = st.text_input(
            "Business Unit (Optional)",
            placeholder="e.g., finance_bu, sales_west",
            help="Filter resources by business unit tag"
        )

        # Role selection
        role = st.selectbox(
            "Role",
            options=["analyst", "engineer", "scientist", "manager"],
            help="Agent's role and expertise level"
        )

    with col2:
        st.markdown("#### Platform")
        platform_name = platform_config.platform.value.title()
        st.info(f"**{platform_name}**\n\nDiscovering from {platform_config.get_storage_label()} catalog tags")

        st.markdown("#### Discovery Scope")
        st.markdown(f"""
        - **Tables** tagged with `domain={selected_domain}`
        - **Metrics** from metric views
        - **Functions** from {platform_config.get_storage_label()}
        """)

    st.markdown("---")

    # Discover button
    if st.button("🔍 Discover Domain Resources", type="primary", use_container_width=True):
        with st.spinner(f"Discovering {selected_domain} domain resources..."):
            try:
                # Perform discovery
                profile = discovery_engine.discover_domain(
                    domain=selected_domain,
                    business_unit=business_unit if business_unit else None
                )

                st.session_state.discovered_profile = profile

                # Show success
                st.success(f"""
                ✅ **Discovery Complete!**

                Found {profile.total_tables} tables, {profile.total_metrics} metrics,
                and {profile.total_functions} functions for {selected_domain} domain.
                """)

                # Show summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Tables Discovered", profile.total_tables)
                with col2:
                    st.metric("Metrics Found", profile.total_metrics)
                with col3:
                    st.metric("Functions Available", profile.total_functions)

            except Exception as e:
                st.error(f"Discovery failed: {str(e)}")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())

    # Show cached profile if available
    if st.session_state.discovered_profile:
        profile = st.session_state.discovered_profile

        st.markdown("---")
        st.markdown("### Quick Preview")

        # Preview tables
        if profile.tables:
            with st.expander(f"📊 Tables ({len(profile.tables)})", expanded=True):
                for table in profile.tables[:5]:
                    st.markdown(f"""
                    <div class="sf-card" style="margin-bottom: 12px;">
                        <div class="sf-card-title">{table.name}</div>
                        <div class="sf-card-description">
                            {table.description or 'No description'}
                        </div>
                        <div style="margin-top: 8px; font-size: 11px; color: var(--sf-text-muted);">
                            Schema: {table.schema} | Type: {table.type}
                            {f' | Columns: {len(table.columns)}' if table.columns else ''}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                if len(profile.tables) > 5:
                    st.caption(f"... and {len(profile.tables) - 5} more tables")

        # Preview metrics
        if profile.metrics:
            with st.expander(f"📈 Metrics ({len(profile.metrics)})"):
                for metric in profile.metrics:
                    st.markdown(f"- **{metric.name}**: {metric.description or 'No description'}")

# TAB 2: CREATE AGENT
with tab2:
    st.markdown("### Create Domain-Specialized Agent")

    if not st.session_state.discovered_profile:
        st.info("👈 First, discover domain resources in the 'Discover Domain' tab")
    else:
        profile = st.session_state.discovered_profile

        st.markdown(f"""
        <div class="sf-card" style="background: var(--sf-primary-light); margin-bottom: 24px;">
            <div style="font-weight: 600; margin-bottom: 8px;">Discovery Summary</div>
            <div style="font-size: 13px;">
                Domain: <strong>{profile.domain}</strong> |
                Tables: <strong>{profile.total_tables}</strong> |
                Metrics: <strong>{profile.total_metrics}</strong> |
                Functions: <strong>{profile.total_functions}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Agent configuration
        col1, col2 = st.columns([2, 1])

        with col1:
            agent_name = st.text_input(
                "Agent Name",
                value=f"{profile.domain.title()} Analyst",
                help="Name for your specialized agent"
            )

            agent_description = st.text_area(
                "Description",
                value=f"Specialized analyst for {profile.domain} domain with access to "
                      f"{profile.total_tables} tables and {profile.total_metrics} metrics",
                height=80
            )

        with col2:
            model_provider = st.selectbox(
                "Model Provider",
                options=platform_config.get_model_providers(),
                index=0
            )

            if model_provider == "openai":
                model_name = st.selectbox("Model", ["gpt-4", "gpt-3.5-turbo"])
            elif model_provider == "anthropic":
                model_name = st.selectbox("Model", ["claude-3-opus", "claude-3-sonnet"])
            else:
                model_name = "default"

            temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)

        # Show auto-generated system prompt
        st.markdown("#### Auto-Generated System Prompt")

        # Generate agent config
        agent_config = discovery_engine.create_domain_agent_config(
            domain=profile.domain,
            business_unit=profile.business_unit,
            role=role if 'role' in locals() else "analyst"
        )

        system_prompt = agent_config["system_prompt"]

        with st.expander("View System Prompt", expanded=True):
            st.code(system_prompt, language="markdown")

        # Tools configuration
        st.markdown("#### Tools & Capabilities")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Auto-Selected Tools:**")
            auto_tools = agent_config.get("tools", [])
            for tool in auto_tools[:5]:
                st.markdown(f"- ✅ {tool}")
            if len(auto_tools) > 5:
                st.caption(f"... and {len(auto_tools) - 5} more")

        with col2:
            st.markdown("**Additional Options:**")
            enable_memory = st.checkbox("Enable Conversation Memory", value=True)
            enable_rag = st.checkbox("Enable RAG (if knowledge base exists)", value=False)
            is_public = st.checkbox("Share in Marketplace", value=False)

        # Create agent button
        st.markdown("---")

        if st.button("🤖 Create Agent", type="primary", use_container_width=True):
            with st.spinner("Creating specialized agent..."):
                try:
                    from agent_builder import AgentConfig

                    # Create agent
                    agent = AgentConfig(
                        id=f"domain-{profile.domain}-{datetime.now().timestamp()}",
                        name=agent_name,
                        description=agent_description,
                        system_prompt=system_prompt,
                        model_provider=model_provider,
                        model_name=model_name,
                        temperature=temperature,
                        max_tokens=2000,
                        enable_memory=enable_memory,
                        memory_type="conversation_buffer",
                        tools=[],  # Tools would be configured based on discovered functions
                        is_public=is_public,
                        tags=[profile.domain, "auto-discovered"],
                        metadata={
                            "domain": profile.domain,
                            "business_unit": profile.business_unit,
                            "auto_discovered": True,
                            "discovered_at": profile.discovered_at,
                            "tables_count": profile.total_tables,
                            "metrics_count": profile.total_metrics,
                            "functions_count": profile.total_functions,
                        }
                    )

                    # Save agent
                    agent_builder.save_agent(agent)

                    st.success(f"""
                    ✅ **Agent Created Successfully!**

                    **{agent_name}** is now available with access to:
                    - {profile.total_tables} domain-specific tables
                    - {profile.total_metrics} pre-defined metrics
                    - {profile.total_functions} specialized functions

                    You can now use this agent in the main chat interface.
                    """)

                    # Clear session state
                    st.session_state.discovered_profile = None

                except Exception as e:
                    st.error(f"Failed to create agent: {str(e)}")
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())

# TAB 3: DISCOVERED RESOURCES
with tab3:
    st.markdown("### Discovered Resources")

    if not st.session_state.discovered_profile:
        st.info("No resources discovered yet. Start discovery in the 'Discover Domain' tab.")
    else:
        profile = st.session_state.discovered_profile

        # Export option
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("📥 Export as JSON"):
                profile_json = json.dumps(profile.to_dict(), indent=2)
                st.download_button(
                    label="Download JSON",
                    data=profile_json,
                    file_name=f"{profile.domain}_resources.json",
                    mime="application/json"
                )

        with col2:
            if st.button("🔄 Refresh Discovery"):
                st.session_state.discovered_profile = None
                st.rerun()

        st.markdown("---")

        # Detailed tables view
        st.markdown("### Tables")
        for table in profile.tables:
            with st.expander(f"📊 {table.name}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Description:** {table.description or 'No description'}")
                    st.markdown(f"**Type:** {table.type}")
                    st.markdown(f"**Schema:** {table.schema}")

                    if table.columns:
                        st.markdown("**Columns:**")
                        for col in table.columns:
                            st.markdown(
                                f"- `{col['name']}` ({col['type']})"
                                + (f" - {col['description']}" if col.get('description') else "")
                            )

                with col2:
                    if table.tags:
                        st.markdown("**Tags:**")
                        for key, value in table.tags.items():
                            st.markdown(f"- {key}: `{value}`")

                if table.sample_queries:
                    st.markdown("**Sample Queries:**")
                    for query in table.sample_queries:
                        st.code(query, language="sql")

        # Metrics view
        if profile.metrics:
            st.markdown("---")
            st.markdown("### Metrics")
            for metric in profile.metrics:
                st.markdown(f"""
                <div class="sf-card">
                    <div class="sf-card-title">{metric.name}</div>
                    <div class="sf-card-description">{metric.description or 'No description'}</div>
                </div>
                """, unsafe_allow_html=True)

        # Functions view
        if profile.functions:
            st.markdown("---")
            st.markdown("### Functions")
            for func in profile.functions:
                st.markdown(f"- **{func.name}**: {func.description or 'No description'}")

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 0; border-bottom: 1px solid var(--sf-border); margin-bottom: 20px;">
        <div style="font-weight: 600; font-size: 16px;">Domain Discovery</div>
        <div style="font-size: 12px; color: var(--sf-text-muted);">Intelligent Resource Discovery</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### How It Works")
    st.markdown("""
    1. **Tag Your Tables**
       - Add domain tags in Unity Catalog/Snowflake
       - Example: `{"domain": "finance"}`

    2. **Discover Resources**
       - Engine queries catalog metadata
       - Finds tables, metrics, functions

    3. **Auto-Configure Agent**
       - Generates specialized system prompt
       - Configures relevant tools
       - Adds sample queries

    4. **Start Using**
       - Agent has full context
       - Pre-approved functions only
       - Domain-specific knowledge
    """)

    st.markdown("---")
    st.markdown("### Tagging Examples")

    st.markdown("**Databricks:**")
    st.code('''
-- Tag table with domain
ALTER TABLE sales.transactions
SET TAGS (
  'domain' = 'finance',
  'business_unit' = 'finance_bu'
);
''', language="sql")

    st.markdown("**Snowflake:**")
    st.code('''
-- Create tag
CREATE TAG domain;

-- Tag table
ALTER TABLE revenue
  SET TAG domain = 'finance';
''', language="sql")

    st.markdown("---")
    st.markdown("### Benefits")
    st.markdown("""
    - ✅ **Zero Manual Configuration**
    - ✅ **Always Up-to-Date**
    - ✅ **Governed Access**
    - ✅ **Domain Expertise**
    - ✅ **Faster Onboarding**
    """)

st.markdown("</div>", unsafe_allow_html=True)
