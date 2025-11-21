# Cortex AI - Modern Enterprise Chatbot

A Snowflake-style AI chatbot built with Streamlit, LangChain, and custom enterprise UI.

## Features

- **Custom Enterprise UI**: Snowflake-inspired design that doesn't look like Streamlit
- **LangChain Integration**: Supports OpenAI and Anthropic models with conversation memory
- **Streaming Responses**: Real-time streaming with markdown and code block support
- **SQL Explorer**: Built-in SQL panel with query execution
- **Data Connectors**: Ready-to-use Snowflake and Databricks integrations

## Project Structure

```
streamlit-prototype/
├── app.py                    # Main Streamlit application
├── ui.py                     # UI components and rendering
├── chat.py                   # LangChain chat engine
├── styles.css                # Custom CSS theme
├── requirements.txt          # Python dependencies
├── components/               # Custom Streamlit components
├── utils/                    # Utility modules
│   └── data_connectors.py    # Snowflake/Databricks connectors
└── assets/                   # Static assets
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
