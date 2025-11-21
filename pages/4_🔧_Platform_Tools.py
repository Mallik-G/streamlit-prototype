"""
Platform Tools Registry - Browse and manage Unity Catalog Functions (Databricks)
or Snowflake UDFs/Stored Procedures
"""
import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui import load_custom_css, render_header, render_sidebar_section
from config import get_platform_config
from utils.platform_tools import get_platform_tools

# Page configuration
st.set_page_config(
    page_title="Platform Tools - Cortex AI",
    page_icon="🔧",
    layout="wide"
)

# Load custom CSS
load_custom_css()

# Initialize
platform_config = get_platform_config()

render_header("Platform Tools Registry", "Governed Tools & Metrics")

st.markdown("""
<div style="padding: 24px; max-width: 1400px; margin: 0 auto;">
""", unsafe_allow_html=True)

# Platform indicator
st.markdown(f"""
<div style="background: var(--sf-primary-light); border: 1px solid var(--sf-primary);
            border-radius: 8px; padding: 16px; margin-bottom: 24px;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 36px;">{platform_config.get_platform_icon()}</span>
        <div style="flex: 1;">
            <div style="font-weight: 600; font-size: 16px;">{platform_config.get_platform_name()} Tools Registry</div>
            <div style="font-size: 13px; color: var(--sf-text-muted); margin-top: 4px;">
                Discover and manage platform-registered functions and metrics for secure agent access
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["🔧 Registered Functions", "📊 Metrics & Semantic Layer", "⚙️ Configuration"])

# TAB 1: Registered Functions
with tab1:
    st.markdown("### Platform-Registered Functions")

    if platform_config.is_databricks():
        st.markdown("""
        Browse functions registered in **Unity Catalog**. These functions can be used as secure tools by agents.

        **Why use UC Functions?**
        - ✅ Controlled access - Only pre-approved functions
        - ✅ Centrally managed - IT governs available tools
        - ✅ Auditable - All function calls logged
        - ✅ No arbitrary code execution
        """)
    elif platform_config.is_snowflake():
        st.markdown("""
        Browse **User-Defined Functions (UDFs)** and **Stored Procedures** in Snowflake. These can be used as secure tools by agents.

        **Why use Snowflake UDFs?**
        - ✅ Controlled access - Only registered functions
        - ✅ Database governance - Security through Snowflake RBAC
        - ✅ Auditable - Query history tracks all calls
        - ✅ No external dependencies
        """)
    else:
        st.info("Platform tools are only available for Snowflake or Databricks deployments.")

    st.markdown("<br>", unsafe_allow_html=True)

    if not platform_config.is_local():
        # Connection configuration
        col1, col2 = st.columns([3, 1])

        with col1:
            if platform_config.is_databricks():
                catalog = st.text_input(
                    "Unity Catalog",
                    value=os.getenv("DATABRICKS_CATALOG", "main"),
                    help="Catalog to scan for functions"
                )
                schema = st.text_input(
                    "Schema (optional)",
                    placeholder="Leave empty to scan all schemas",
                    help="Filter functions by schema"
                )
            else:  # Snowflake
                database = st.text_input(
                    "Database",
                    value=os.getenv("SNOWFLAKE_DATABASE", ""),
                    help="Database to scan for UDFs"
                )
                schema = st.text_input(
                    "Schema (optional)",
                    value=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
                    help="Filter UDFs by schema"
                )

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            discover_btn = st.button("🔍 Discover Functions", type="primary", use_container_width=True)

        # Discover and display functions
        if discover_btn or st.session_state.get('discovered_tools'):
            with st.spinner("Discovering platform functions..."):
                try:
                    tool_manager = get_platform_tools(platform_config.platform.value)
                    tools = tool_manager.discover_all_tools()

                    # Cache discovered tools
                    st.session_state.discovered_tools = tools

                    if not tools:
                        st.warning("No functions found. Make sure functions are registered in your platform and you have access.")
                    else:
                        st.success(f"✅ Found {len(tools)} registered functions")

                        # Display tools
                        for tool in tools:
                            with st.expander(f"🔧 {tool.function_name} ({tool.schema})"):
                                col1, col2 = st.columns([2, 1])

                                with col1:
                                    st.markdown(f"**Description:** {tool.description}")
                                    st.markdown(f"**Full Name:** `{tool.id}`")
                                    st.markdown(f"**Return Type:** `{tool.return_type}`")

                                    if tool.input_params:
                                        st.markdown("**Parameters:**")
                                        for param in tool.input_params:
                                            st.markdown(f"- `{param['name']}`: {param['type']}")
                                    else:
                                        st.markdown("**Parameters:** None")

                                with col2:
                                    st.markdown(f"""
                                    <div class="sf-card">
                                        <div style="font-size: 11px; color: var(--sf-text-muted);">
                                            <div><strong>Type:</strong> {tool.function_type.upper()}</div>
                                            <div><strong>Platform:</strong> {tool.platform.title()}</div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)

                                if tool.example_usage:
                                    st.markdown("**Example Usage:**")
                                    st.code(tool.example_usage, language="sql")

                                # Test function
                                if st.button(f"Test {tool.function_name}", key=f"test_{tool.id}"):
                                    st.info("Function testing coming soon!")

                except Exception as e:
                    st.error(f"Error discovering functions: {str(e)}")
                    import traceback
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())

# TAB 2: Metrics & Semantic Layer
with tab2:
    st.markdown("### Metrics & Semantic Layer")

    if platform_config.is_databricks():
        st.markdown("""
        Browse **Metric Views** from Unity Catalog. Use predefined metrics instead of on-the-fly calculations.

        **Benefits:**
        - ✅ Consistent definitions across organization
        - ✅ Pre-calculated for performance
        - ✅ Governed metric logic
        - ✅ Standard business definitions
        """)

        st.markdown("#### Unity Catalog Metric Views")

    elif platform_config.is_snowflake():
        st.markdown("""
        Browse **Semantic Layer** models from Snowflake. Use standard metrics with consistent definitions.

        **Benefits:**
        - ✅ Single source of truth for metrics
        - ✅ Optimized query performance
        - ✅ Governed business logic
        - ✅ Standard metric definitions
        """)

        st.markdown("#### Snowflake Semantic Models")

    else:
        st.info("Metrics and semantic layers are only available for Snowflake or Databricks deployments.")

    st.markdown("<br>", unsafe_allow_html=True)

    if not platform_config.is_local():
        if st.button("🔍 Discover Metrics", type="primary"):
            with st.spinner("Discovering metrics..."):
                try:
                    tool_manager = get_platform_tools(platform_config.platform.value)
                    metrics = tool_manager.get_metrics()

                    if not metrics:
                        st.warning("No metrics found. Create metric views tagged with 'metric' in the name or comment.")
                    else:
                        st.success(f"✅ Found {len(metrics)} metrics")

                        # Display metrics
                        for metric in metrics:
                            st.markdown(f"""
                            <div class="sf-card">
                                <div style="display: flex; align-items: start; gap: 12px;">
                                    <div style="font-size: 32px;">📊</div>
                                    <div style="flex: 1;">
                                        <div class="sf-card-title">{metric['name']}</div>
                                        <div class="sf-card-description">{metric['description']}</div>
                                        <div style="margin-top: 8px; font-size: 11px; color: var(--sf-text-muted);">
                                            <code>{metric['full_name']}</code>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            col1, col2, col3 = st.columns(3)

                            with col1:
                                if st.button("📊 Preview Data", key=f"preview_{metric['name']}"):
                                    try:
                                        result = tool_manager.query_metric(metric['full_name'])
                                        if result:
                                            st.dataframe(result, use_container_width=True)
                                        else:
                                            st.warning("No data returned")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")

                            with col2:
                                if st.button("📋 Schema", key=f"schema_{metric['name']}"):
                                    st.info("Schema inspection coming soon!")

                            st.markdown("<br>", unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Error discovering metrics: {str(e)}")

# TAB 3: Configuration
with tab3:
    st.markdown("### Platform Configuration")

    if platform_config.is_databricks():
        st.markdown("#### Databricks Unity Catalog Configuration")

        st.code("""
# Environment Variables
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/abc123"
export DATABRICKS_TOKEN="dapi..."
export DATABRICKS_CATALOG="main"
        """, language="bash")

        st.markdown("#### Create a UC Function")

        st.code("""
-- SQL Function
CREATE FUNCTION main.default.calculate_revenue(
    price DOUBLE,
    quantity INT
)
RETURNS DOUBLE
COMMENT 'Calculate total revenue from price and quantity'
RETURN price * quantity;

-- Python Function
CREATE FUNCTION main.default.sentiment_analysis(text STRING)
RETURNS STRING
LANGUAGE PYTHON
COMMENT 'Analyze sentiment of text'
AS $$
    # Your Python code here
    return "positive" if "good" in text.lower() else "negative"
$$;
        """, language="sql")

        st.markdown("#### Create Metric Views")

        st.code("""
-- Create a metric view
CREATE VIEW main.default.sales_metrics AS
SELECT
    date_trunc('day', order_date) as date,
    COUNT(*) as order_count,
    SUM(revenue) as total_revenue,
    AVG(revenue) as avg_order_value
FROM main.default.orders
GROUP BY date_trunc('day', order_date);

-- Tag as metric
COMMENT ON VIEW main.default.sales_metrics IS
'Daily sales metrics including order count, revenue, and AOV';
        """, language="sql")

    elif platform_config.is_snowflake():
        st.markdown("#### Snowflake Configuration")

        st.code("""
# Environment Variables
export SNOWFLAKE_ACCOUNT="your_account"
export SNOWFLAKE_USER="your_user"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
export SNOWFLAKE_DATABASE="MY_DB"
export SNOWFLAKE_SCHEMA="PUBLIC"
        """, language="bash")

        st.markdown("#### Create UDFs")

        st.code("""
-- SQL UDF
CREATE FUNCTION calculate_discount(price FLOAT, discount_pct FLOAT)
RETURNS FLOAT
COMMENT = 'Calculate discounted price'
AS
$$
    price * (1 - discount_pct / 100)
$$;

-- JavaScript UDF
CREATE FUNCTION parse_json_field(json_str STRING, field_name STRING)
RETURNS STRING
LANGUAGE JAVASCRIPT
COMMENT = 'Extract field from JSON string'
AS
$$
    try {
        const obj = JSON.parse(JSON_STR);
        return obj[FIELD_NAME];
    } catch (e) {
        return null;
    }
$$;

-- Python UDF
CREATE FUNCTION classify_text(text STRING)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.8'
HANDLER = 'classify'
COMMENT = 'Classify text into categories'
AS
$$
def classify(text):
    # Your classification logic
    return "category"
$$;
        """, language="sql")

        st.markdown("#### Create Semantic Layer Views")

        st.code("""
-- Create semantic metric view
CREATE VIEW revenue_metrics AS
SELECT
    DATE_TRUNC('month', order_date) as month,
    region,
    COUNT(DISTINCT customer_id) as unique_customers,
    SUM(order_amount) as total_revenue,
    AVG(order_amount) as avg_revenue_per_order
FROM orders
GROUP BY DATE_TRUNC('month', order_date), region;

COMMENT ON VIEW revenue_metrics IS
'semantic: Monthly revenue metrics by region';
        """, language="sql")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Security Best Practices")

    st.markdown("""
    **Function Security:**
    1. ✅ Only register trusted functions
    2. ✅ Use RBAC to control function access
    3. ✅ Review function code before registration
    4. ✅ Avoid functions that call external APIs
    5. ✅ Log all function executions

    **Metric Governance:**
    1. ✅ Define metrics centrally
    2. ✅ Document metric calculations
    3. ✅ Version metric definitions
    4. ✅ Control who can create metrics
    5. ✅ Regular metric reviews
    """)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 0; border-bottom: 1px solid var(--sf-border); margin-bottom: 20px;">
        <div style="font-weight: 600; font-size: 16px;">Platform Tools</div>
        <div style="font-size: 12px; color: var(--sf-text-muted);">Governed Access</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔒 Security Benefits")

    st.markdown("""
    **vs. Arbitrary Tools:**
    - ❌ Web search
    - ❌ Code execution
    - ❌ External APIs
    - ❌ File access

    **Platform Tools:**
    - ✅ Pre-approved only
    - ✅ Centrally managed
    - ✅ Fully auditable
    - ✅ RBAC controlled
    """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📚 Resources")

    if platform_config.is_databricks():
        st.markdown("""
        **Databricks Docs:**
        - [Unity Catalog Functions](https://docs.databricks.com)
        - [Create Functions](https://docs.databricks.com)
        - [Function Security](https://docs.databricks.com)
        """)
    elif platform_config.is_snowflake():
        st.markdown("""
        **Snowflake Docs:**
        - [UDFs](https://docs.snowflake.com/en/sql-reference/udf-overview)
        - [Stored Procedures](https://docs.snowflake.com/en/sql-reference/stored-procedures)
        - [Function Security](https://docs.snowflake.com)
        """)

st.markdown("</div>", unsafe_allow_html=True)
