# Cortex AI - Modern Enterprise Chatbot

A modern AI chatbot platform with Snowflake/Databricks integration, built with Streamlit, LangChain, and custom enterprise UI.

## Features

### Core Platform
- **Custom Enterprise UI**: Snowflake/Databricks-inspired design with professional styling
- **LangChain Integration**: Supports OpenAI and Anthropic models with conversation memory
- **Streaming Responses**: Real-time streaming with markdown and code block support
- **Multi-Platform Support**: Configured for Snowflake, Databricks, or local deployment
- **Data Connectors**: Ready-to-use Snowflake and Databricks integrations

### Agent Builder
- **Self-Serve Agent Creation**: Build custom AI agents without code (inspired by [Databricks Labs Kasal](https://github.com/databrickslabs/kasal))
- **Agent Marketplace**: Discover and deploy pre-built agents from the community
- **Agent Templates**: 9 pre-configured agents for common use cases
- **RAG Integration**: Connect agents to knowledge bases via vector search

### Knowledge Base & Vector Search
- **Document Upload**: Ingest PDF, DOCX, TXT, MD, CSV files
- **Platform-Native Storage**: Snowflake Stages or Databricks Volumes
- **Vector Search**: Cortex Search (Snowflake), Vector Search (Databricks), or ChromaDB (local)
- **RAG Support**: Document-based context retrieval for agents

### Platform Tools (Governed Access)
- **Unity Catalog Functions** (Databricks): Use UC-registered functions as agent tools
- **Snowflake UDFs**: Leverage Snowflake UDFs and stored procedures
- **Metric Views**: Standard metric definitions from Databricks or Snowflake semantic layer
- **Security-First**: Controlled access, no arbitrary web search or code execution

### Workflow Builder
- **Multi-Agent Orchestration**: Chain multiple agents for complex workflows
- **Execution Modes**: Sequential, Parallel, or DAG-based execution
- **Form-Based Configuration**: Build workflows via intuitive forms
- **YAML Storage**: Version-controllable workflow definitions
- **Mermaid Visualization**: Auto-generated workflow diagrams
- **Workflow Templates**: Pre-built pipelines for common use cases

## Project Structure

```
streamlit-prototype/
├── app.py                          # Main Streamlit application with chat interface
├── ui.py                           # Custom UI components and rendering
├── chat.py                         # LangChain chat engine with streaming
├── styles.css                      # Custom Snowflake/Databricks CSS theme
├── config.py                       # Global platform configuration
├── agent_builder.py                # Agent creation and management
├── agent_templates.py              # Pre-built agent templates
├── workflow_builder.py             # Multi-agent workflow orchestration
├── requirements.txt                # Python dependencies
├── AGENT_BUILDER_GUIDE.md          # Agent builder documentation
├── pages/                          # Streamlit pages (multi-page app)
│   ├── 1_🔧_Agent_Builder.py      # Agent builder UI
│   ├── 2_🏪_Agent_Marketplace.py  # Agent marketplace UI
│   ├── 3_📚_Knowledge_Base.py     # Document upload & vector search
│   ├── 4_🔧_Platform_Tools.py     # UC Functions / Snowflake UDFs registry
│   └── 5_📊_Workflow_Builder.py   # Workflow builder UI
├── components/                     # Custom Streamlit components
├── utils/                          # Utility modules
│   ├── __init__.py                 # Package initialization
│   ├── data_connectors.py          # Snowflake/Databricks connectors
│   ├── vector_search.py            # Multi-platform vector search
│   └── platform_tools.py           # Platform-native tool discovery
├── agents/                         # Agent storage (JSON, created at runtime)
├── workflows/                      # Workflow storage (YAML, created at runtime)
├── vector_stores/                  # Vector search indexes (created at runtime)
└── assets/                         # Static assets
```

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables (optional)

```bash
# API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Platform Configuration (set one)
DEPLOYMENT_PLATFORM=local|snowflake|databricks

# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=your_role  # optional

# Databricks Configuration
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/abc123
DATABRICKS_TOKEN=dapi...
DATABRICKS_CATALOG=main
```

## Running the App

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Quick Start Guide

### 1. Agent Builder

Create custom AI agents without code:

1. **Navigate to Agent Builder** (🔧 Agent Builder page)
2. **Choose a template** or create from scratch
3. **Configure**:
   - Name and description
   - Model provider and temperature
   - System prompt and personality
   - Tools and capabilities
   - RAG/Knowledge base (optional)
4. **Create & Test** your agent
5. **Publish** to marketplace (optional)

**Pre-built Agent Templates:**
- 📊 Data Analyst - Statistical analysis and insights
- 💾 SQL Expert - Query optimization specialist
- 💬 Customer Support - Friendly support agent
- ✍️ Content Writer - Marketing and creative content
- 🐍 Python Developer - Code development assistant
- 🔬 Research Assistant - Comprehensive researcher
- 📈 BI Analyst - Business intelligence expert
- 🧱 Databricks Expert - Spark and Delta Lake specialist
- ❄️ Snowflake Expert - Data warehouse optimization

See [AGENT_BUILDER_GUIDE.md](AGENT_BUILDER_GUIDE.md) for complete documentation.

### 2. Knowledge Base & RAG

Enable document-based context for your agents:

1. **Navigate to Knowledge Base** (📚 Knowledge Base page)
2. **Create a Vector Search Index**:
   - Choose embedding model (platform-specific)
   - Select storage location (Stage/Volume)
   - Configure chunking strategy
3. **Upload Documents**:
   - Support for PDF, DOCX, TXT, MD, CSV
   - Automatic chunking and embedding
   - Progress tracking
4. **Connect to Agents**:
   - Enable RAG in Agent Builder
   - Select knowledge base
   - Agents can now query documents

**Platform-Specific:**
- **Snowflake**: Uses Stages for storage, Cortex Search for vector search, Cortex embeddings
- **Databricks**: Uses Volumes for storage, Vector Search, BAAI/bge-large-en embeddings
- **Local**: Uses ChromaDB with sentence-transformers

### 3. Platform Tools (Governed Access)

Use pre-approved platform functions as agent tools:

1. **Navigate to Platform Tools** (🔧 Platform Tools page)
2. **Discover Functions**:
   - Unity Catalog Functions (Databricks)
   - Snowflake UDFs and Stored Procedures
3. **Browse Metrics**:
   - Metric Views (Databricks)
   - Semantic Layer Models (Snowflake)
4. **Use in Agents**:
   - Functions appear as available tools
   - No arbitrary code execution
   - Fully governed and auditable

**Security Benefits:**
- Only pre-approved functions
- Centrally managed by IT/Data teams
- Complete audit trail
- No web search or external API access

### 4. Workflow Builder

Create multi-agent workflows for complex tasks:

1. **Navigate to Workflow Builder** (📊 Workflow Builder page)
2. **Create Workflow**:
   - Name and description
   - Choose execution mode (Sequential/Parallel/DAG)
   - Add workflow steps
3. **Configure Steps**:
   - Assign agent to each step
   - Define task description
   - Set input/output variables
   - Configure dependencies (DAG mode)
   - Add platform tools
4. **Preview**:
   - View Mermaid diagram
   - Inspect YAML configuration
5. **Execute**:
   - Provide initial context
   - Monitor step-by-step execution
   - View results and final context

**Execution Modes:**
- **Sequential**: Steps run one after another, output feeds into next step
- **Parallel**: All steps run simultaneously for maximum speed
- **DAG**: Steps run based on dependencies, optimized parallelism

**Workflow Templates:**
- 🔬 Research & Analysis Pipeline (Research → Analyze → Report)
- 📊 Data Analysis Pipeline (Extract → Analyze → Visualize → Report)
- ✍️ Content Creation Workflow (Research → Draft → Review → Publish)

## UI Customization

The app uses a Snowflake-inspired design language. To switch to Databricks style, modify CSS variables in `styles.css`:

```css
:root {
    --sf-primary: #FF3621;      /* Databricks orange */
    --sf-secondary: #00A972;    /* Databricks green */
}
```

## License

MIT License
