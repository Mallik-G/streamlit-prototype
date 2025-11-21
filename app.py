"""
Cortex AI - Modern Enterprise Chatbot
A Snowflake-style AI assistant built with Streamlit and LangChain
"""
import streamlit as st
from ui import (
    load_custom_css,
    render_header,
    render_message,
    render_welcome,
    render_sidebar_section,
    render_sql_panel,
    render_data_table,
    render_loading
)
from chat import ChatEngine, Message
from utils.data_connectors import get_connector

# Page configuration
st.set_page_config(
    page_title="Cortex AI",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_custom_css()

# Initialize session state
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chat_engine" not in st.session_state:
        st.session_state.chat_engine = None
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    if "db_connector" not in st.session_state:
        st.session_state.db_connector = None
    if "show_sql_panel" not in st.session_state:
        st.session_state.show_sql_panel = False

init_session_state()


def init_chat_engine(model: str, provider: str, system_prompt: str, enable_memory: bool):
    """Initialize or reinitialize the chat engine"""
    st.session_state.chat_engine = ChatEngine(
        model_name=model,
        provider=provider,
        system_prompt=system_prompt,
        enable_memory=enable_memory
    )
    # Restore existing messages
    for msg in st.session_state.messages:
        st.session_state.chat_engine.messages.append(
            Message(role=msg["role"], content=msg["content"])
        )


# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 0; border-bottom: 1px solid var(--sf-border); margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #29B5E8, #249EBF);
                        border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                <svg width="24" height="24" viewBox="0 0 40 40" fill="none">
                    <path d="M20 8L26 14L20 20L14 14L20 8Z" fill="white"/>
                    <path d="M14 14L20 20L14 26L8 20L14 14Z" fill="white" fill-opacity="0.8"/>
                    <path d="M26 14L32 20L26 26L20 20L26 14Z" fill="white" fill-opacity="0.8"/>
                </svg>
            </div>
            <div>
                <div style="font-weight: 600; font-size: 16px;">Cortex AI</div>
                <div style="font-size: 12px; color: var(--sf-text-muted);">Settings</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Model Settings Section
    render_sidebar_section("MODEL CONFIGURATION")

    provider = st.selectbox(
        "Provider",
        options=["openai", "anthropic"],
        index=0,
        help="Select the AI provider"
    )

    if provider == "openai":
        model_options = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
    else:
        model_options = ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]

    model = st.selectbox(
        "Model",
        options=model_options,
        index=0,
        help="Select the AI model"
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1,
        help="Controls randomness in responses"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Memory Settings
    render_sidebar_section("CONVERSATION")

    enable_memory = st.toggle(
        "Enable Memory",
        value=True,
        help="Remember conversation context"
    )

    if st.button("Clear History", use_container_width=True):
        st.session_state.messages = []
        if st.session_state.chat_engine:
            st.session_state.chat_engine.clear_history()
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # System Prompt
    render_sidebar_section("SYSTEM PROMPT")

    system_prompt = st.text_area(
        "System Prompt",
        value="""You are Cortex AI, an intelligent assistant specialized in data analysis and SQL queries.
Help users explore data, write optimized queries, and understand complex datasets.""",
        height=120,
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Database Connection
    render_sidebar_section("DATA CONNECTION")

    db_type = st.selectbox(
        "Database",
        options=["Demo Mode", "Snowflake", "Databricks"],
        index=0
    )

    show_sql = st.toggle(
        "Show SQL Panel",
        value=st.session_state.show_sql_panel,
        help="Display SQL query panel"
    )
    st.session_state.show_sql_panel = show_sql

    # Initialize chat engine if needed
    if st.session_state.chat_engine is None:
        init_chat_engine(model, provider, system_prompt, enable_memory)

    # Apply settings button
    if st.button("Apply Settings", use_container_width=True, type="primary"):
        init_chat_engine(model, provider, system_prompt, enable_memory)
        st.toast("Settings applied!", icon="✅")


# Main content area
render_header("Cortex AI", "Intelligent Data Assistant")

# Create layout
if st.session_state.show_sql_panel:
    main_col, sql_col = st.columns([2, 1])
else:
    main_col = st.container()
    sql_col = None

with main_col:
    # Chat container
    st.markdown('<div class="sf-chat-container">', unsafe_allow_html=True)

    # Messages area
    st.markdown('<div class="sf-messages-container" id="messages-container">', unsafe_allow_html=True)

    # Show welcome screen if no messages
    if not st.session_state.messages:
        render_welcome()
    else:
        # Render all messages
        for msg in st.session_state.messages:
            render_message(msg["role"], msg["content"])

    st.markdown('</div>', unsafe_allow_html=True)

    # Input area
    st.markdown('<div class="sf-input-container">', unsafe_allow_html=True)

    # Create input form
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])

        with col1:
            user_input = st.text_area(
                "Message",
                placeholder="Ask me anything about your data...",
                height=80,
                label_visibility="collapsed",
                key="user_input"
            )

        with col2:
            submit = st.form_submit_button(
                "Send",
                type="primary",
                use_container_width=True
            )

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Handle form submission
    if submit and user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Generate response
        with st.spinner(""):
            response_placeholder = st.empty()
            full_response = ""

            # Stream response
            for chunk in st.session_state.chat_engine.generate_response(user_input):
                full_response += chunk
                # Update placeholder with partial response
                response_placeholder.markdown(f"""
                <div class="sf-message sf-message-assistant">
                    <div class="sf-message-avatar">AI</div>
                    <div class="sf-message-content">
                        <div class="sf-message-text">{full_response}▌</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Clear placeholder and add final message to history
            response_placeholder.empty()
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        st.rerun()

# SQL Panel (if enabled)
if sql_col:
    with sql_col:
        st.markdown("""
        <div style="padding: 16px; border-left: 1px solid var(--sf-border); height: 100%;">
        """, unsafe_allow_html=True)

        sql_query, run_query = render_sql_panel()

        if run_query and sql_query:
            # Get connector
            connector_type = "mock" if db_type == "Demo Mode" else db_type.lower()
            connector = get_connector(connector_type)
            connector.connect()

            result = connector.execute_query(sql_query)

            if result.success:
                st.success(f"Query executed in {result.execution_time:.2f}s ({result.row_count} rows)")
                render_data_table(result.data)
            else:
                st.error(f"Error: {result.error}")

            connector.close()

        # Show available tables
        st.markdown("<br>", unsafe_allow_html=True)
        render_sidebar_section("AVAILABLE TABLES")

        connector = get_connector("mock")
        connector.connect()
        tables = connector.get_tables()

        for table in tables:
            with st.expander(f"📊 {table['TABLE_NAME']}"):
                cols = connector.get_columns(table['TABLE_NAME'])
                for col in cols:
                    st.markdown(f"`{col['COLUMN_NAME']}` - {col['DATA_TYPE']}")

        connector.close()
        st.markdown("</div>", unsafe_allow_html=True)


# Auto-scroll JavaScript
st.markdown("""
<script>
    const container = document.getElementById('messages-container');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
</script>
""", unsafe_allow_html=True)
