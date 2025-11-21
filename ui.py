"""
UI Components Module - Snowflake-Style Enterprise UI
"""
import streamlit as st
from datetime import datetime
import re


def load_custom_css():
    """Load custom CSS styles"""
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_header(title: str = "Cortex AI", subtitle: str = "Intelligent Assistant"):
    """Render the custom header with logo"""
    header_html = f"""
    <div class="sf-header">
        <div class="sf-header-logo">
            <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="20" cy="20" r="18" fill="white" fill-opacity="0.15"/>
                <path d="M20 8L26 14L20 20L14 14L20 8Z" fill="white"/>
                <path d="M14 14L20 20L14 26L8 20L14 14Z" fill="white" fill-opacity="0.8"/>
                <path d="M26 14L32 20L26 26L20 20L26 14Z" fill="white" fill-opacity="0.8"/>
                <path d="M20 20L26 26L20 32L14 26L20 20Z" fill="white" fill-opacity="0.6"/>
            </svg>
            <div>
                <div class="sf-header-title">{title}</div>
                <div class="sf-header-subtitle">{subtitle}</div>
            </div>
        </div>
        <div class="sf-header-actions">
            <div class="sf-status-badge sf-status-success">
                <span>●</span> Connected
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


def render_message(role: str, content: str, timestamp: str = None):
    """Render a chat message bubble"""
    if timestamp is None:
        timestamp = datetime.now().strftime("%I:%M %p")

    avatar_text = "AI" if role == "assistant" else "You"
    message_class = f"sf-message sf-message-{role}"

    # Process markdown content for code blocks
    processed_content = process_markdown(content)

    message_html = f"""
    <div class="{message_class}">
        <div class="sf-message-avatar">{avatar_text}</div>
        <div class="sf-message-content">
            <div class="sf-message-text sf-markdown">{processed_content}</div>
            <div class="sf-message-timestamp">{timestamp}</div>
        </div>
    </div>
    """
    st.markdown(message_html, unsafe_allow_html=True)


def process_markdown(content: str) -> str:
    """Process markdown content with custom code block styling"""
    import html

    # Escape HTML first
    content = html.escape(content)

    # Process code blocks with language
    code_block_pattern = r'```(\w+)?\n(.*?)```'

    def replace_code_block(match):
        language = match.group(1) or 'code'
        code = match.group(2)
        return f'''<div class="sf-code-block">
            <div class="sf-code-header">
                <span class="sf-code-language">{language}</span>
                <button class="sf-code-copy" onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.innerText)">Copy</button>
            </div>
            <pre><code>{code}</code></pre>
        </div>'''

    content = re.sub(code_block_pattern, replace_code_block, content, flags=re.DOTALL)

    # Process inline code
    content = re.sub(r'`([^`]+)`', r'<code>\1</code>', content)

    # Process bold
    content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', content)

    # Process italic
    content = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', content)

    # Process line breaks
    content = content.replace('\n', '<br>')

    return content


def render_loading():
    """Render loading animation"""
    loading_html = """
    <div class="sf-loading">
        <div class="sf-message-avatar" style="background: linear-gradient(135deg, #29B5E8 0%, #249EBF 100%); color: white;">AI</div>
        <div class="sf-loading-dots">
            <div class="sf-loading-dot"></div>
            <div class="sf-loading-dot"></div>
            <div class="sf-loading-dot"></div>
        </div>
    </div>
    """
    return st.markdown(loading_html, unsafe_allow_html=True)


def render_welcome():
    """Render welcome screen with suggestions"""
    welcome_html = """
    <div class="sf-welcome">
        <div class="sf-welcome-icon">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 8L26 14L20 20L14 14L20 8Z" fill="white"/>
                <path d="M14 14L20 20L14 26L8 20L14 14Z" fill="white" fill-opacity="0.8"/>
                <path d="M26 14L32 20L26 26L20 20L26 14Z" fill="white" fill-opacity="0.8"/>
                <path d="M20 20L26 26L20 32L14 26L20 20Z" fill="white" fill-opacity="0.6"/>
            </svg>
        </div>
        <h1 class="sf-welcome-title">Welcome to Cortex AI</h1>
        <p class="sf-welcome-subtitle">
            Your intelligent assistant for data exploration, analysis, and insights.
            Ask me anything about your data or get help with SQL queries.
        </p>
        <div class="sf-suggestions">
            <div class="sf-suggestion-card" onclick="document.querySelector('textarea').value='Show me the top 10 customers by revenue'">
                <div class="sf-suggestion-icon">📊</div>
                <div class="sf-suggestion-text">Show me the top 10 customers by revenue</div>
            </div>
            <div class="sf-suggestion-card" onclick="document.querySelector('textarea').value='Write a SQL query to analyze sales trends'">
                <div class="sf-suggestion-icon">💾</div>
                <div class="sf-suggestion-text">Write a SQL query to analyze sales trends</div>
            </div>
            <div class="sf-suggestion-card" onclick="document.querySelector('textarea').value='Explain how to optimize this query'">
                <div class="sf-suggestion-icon">⚡</div>
                <div class="sf-suggestion-text">Help me optimize my SQL queries</div>
            </div>
            <div class="sf-suggestion-card" onclick="document.querySelector('textarea').value='What tables are available in my database?'">
                <div class="sf-suggestion-icon">🗂️</div>
                <div class="sf-suggestion-text">Explore available database tables</div>
            </div>
        </div>
    </div>
    """
    st.markdown(welcome_html, unsafe_allow_html=True)


def render_sidebar_section(title: str):
    """Render a sidebar section with title"""
    st.markdown(f'<div class="sf-sidebar-title">{title}</div>', unsafe_allow_html=True)


def render_sql_panel(query: str = "", results=None):
    """Render SQL explorer panel"""
    panel_html = f"""
    <div class="sf-sql-panel">
        <div class="sf-sql-header">
            <span class="sf-sql-title">SQL Query</span>
            <div class="sf-status-badge sf-status-success">
                <span>●</span> Ready
            </div>
        </div>
    </div>
    """
    st.markdown(panel_html, unsafe_allow_html=True)

    # SQL Editor
    sql_query = st.text_area(
        "sql_editor",
        value=query,
        height=120,
        label_visibility="collapsed",
        placeholder="Enter your SQL query here..."
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        run_query = st.button("Run Query", type="primary", use_container_width=True)

    return sql_query, run_query


def render_data_table(df, title: str = "Query Results"):
    """Render a styled data table"""
    st.markdown(f"""
    <div class="sf-table-container">
        <div class="sf-sql-header">
            <span class="sf-sql-title">{title}</span>
            <span style="color: var(--sf-text-muted); font-size: 12px;">{len(df)} rows</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_card(title: str, content: str, icon: str = None):
    """Render a styled card component"""
    icon_html = f'<span style="font-size: 24px; margin-bottom: 12px; display: block;">{icon}</span>' if icon else ''
    card_html = f"""
    <div class="sf-card">
        {icon_html}
        <div class="sf-card-title">{title}</div>
        <div class="sf-card-description">{content}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_citation(source: str, index: int):
    """Render a citation badge"""
    return f'<span class="sf-citation" title="{source}">[{index}]</span>'
