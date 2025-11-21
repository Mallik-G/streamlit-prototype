# Cortex AI - Modern Enterprise Chatbot

A Snowflake-style AI chatbot built with Streamlit, LangChain, and custom enterprise UI.

## Features

- **Custom Enterprise UI**: Snowflake-inspired design that doesn't look like Streamlit
- **LangChain Integration**: Supports OpenAI and Anthropic models with conversation memory
- **Streaming Responses**: Real-time streaming with markdown and code block support
- **SQL Explorer**: Built-in SQL panel with query execution
- **Data Connectors**: Ready-to-use Snowflake and Databricks integrations
- **Agent Builder**: Self-serve platform for creating, deploying, and sharing custom AI agents (inspired by [Databricks Labs Kasal](https://github.com/databrickslabs/kasal))
- **Agent Marketplace**: Discover and deploy pre-built agents from the community
- **Agent Templates**: 9 pre-configured agents for common use cases

## Project Structure

```
streamlit-prototype/
├── app.py                          # Main Streamlit application
├── ui.py                           # UI components and rendering
├── chat.py                         # LangChain chat engine
├── styles.css                      # Custom CSS theme
├── agent_builder.py                # Agent creation and management
├── agent_templates.py              # Pre-built agent templates
├── requirements.txt                # Python dependencies
├── AGENT_BUILDER_GUIDE.md          # Agent builder documentation
├── pages/                          # Streamlit pages
│   ├── 1_🔧_Agent_Builder.py      # Agent builder UI
│   └── 2_🏪_Agent_Marketplace.py  # Agent marketplace UI
├── components/                     # Custom Streamlit components
├── utils/                          # Utility modules
│   └── data_connectors.py          # Snowflake/Databricks connectors
├── agents/                         # Agent storage (created at runtime)
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

# Snowflake
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database

# Databricks
DATABRICKS_HOST=your_host
DATABRICKS_HTTP_PATH=your_http_path
DATABRICKS_TOKEN=your_token
```

## Running the App

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Agent Builder

Create and deploy custom AI agents without code:

### Quick Start

1. **Navigate to Agent Builder** (🔧 icon in sidebar)
2. **Choose a template** or create from scratch
3. **Configure**:
   - Name and description
   - Model and temperature
   - System prompt
   - Tools and capabilities
4. **Create & Test** your agent
5. **Publish** to marketplace (optional)

### Pre-built Templates

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
