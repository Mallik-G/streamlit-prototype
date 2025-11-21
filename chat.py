"""
Chat Module - LangChain Integration for AI Chatbot
"""
import os
from typing import Generator, Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    """Chat message data class"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str = None
    citations: List[Dict[str, str]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().strftime("%I:%M %p")
        if self.citations is None:
            self.citations = []


class ChatEngine:
    """LangChain-powered chat engine with memory and tools"""

    def __init__(
        self,
        model_name: str = "gpt-4",
        provider: str = "openai",
        temperature: float = 0.7,
        system_prompt: str = None,
        enable_memory: bool = True,
        api_key: str = None
    ):
        self.model_name = model_name
        self.provider = provider
        self.temperature = temperature
        self.enable_memory = enable_memory
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.messages: List[Message] = []

        # Initialize LangChain components
        self.llm = None
        self.memory = None
        self.chain = None
        self._initialize_chain()

    def _default_system_prompt(self) -> str:
        return """You are Cortex AI, an intelligent assistant specialized in data analysis,
SQL queries, and business insights. You help users explore their data, write optimized queries,
and understand complex datasets.

Key capabilities:
- Write and explain SQL queries for various databases (Snowflake, Databricks, PostgreSQL)
- Analyze data patterns and provide insights
- Help with data modeling and schema design
- Optimize query performance
- Explain technical concepts clearly

Always be helpful, accurate, and concise. When providing SQL queries, format them properly
with syntax highlighting. When referencing data sources, cite them appropriately."""

    def _initialize_chain(self):
        """Initialize LangChain components"""
        try:
            if self.provider == "openai":
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model=self.model_name,
                    temperature=self.temperature,
                    api_key=self.api_key,
                    streaming=True
                )
            elif self.provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                self.llm = ChatAnthropic(
                    model=self.model_name,
                    temperature=self.temperature,
                    api_key=self.api_key,
                    streaming=True
                )

            if self.enable_memory:
                from langchain.memory import ConversationBufferMemory
                self.memory = ConversationBufferMemory(
                    return_messages=True,
                    memory_key="chat_history"
                )

        except ImportError as e:
            print(f"LangChain import error: {e}")
            print("Running in demo mode without LangChain")
            self.llm = None

    def add_message(self, role: str, content: str) -> Message:
        """Add a message to the conversation history"""
        msg = Message(role=role, content=content)
        self.messages.append(msg)
        return msg

    def get_messages(self) -> List[Message]:
        """Get all messages in the conversation"""
        return self.messages

    def clear_history(self):
        """Clear conversation history"""
        self.messages = []
        if self.memory:
            self.memory.clear()

    def generate_response(self, user_input: str) -> Generator[str, None, None]:
        """Generate a streaming response"""
        self.add_message("user", user_input)

        if self.llm is None:
            # Demo mode - simulate streaming response
            yield from self._demo_response(user_input)
            return

        try:
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

            # Build messages list
            messages = [SystemMessage(content=self.system_prompt)]

            # Add conversation history
            for msg in self.messages[:-1]:  # Exclude current message
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                else:
                    messages.append(AIMessage(content=msg.content))

            # Add current message
            messages.append(HumanMessage(content=user_input))

            # Stream response
            full_response = ""
            for chunk in self.llm.stream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    full_response += chunk.content
                    yield chunk.content

            # Save assistant response
            self.add_message("assistant", full_response)

            # Update memory if enabled
            if self.memory:
                self.memory.save_context(
                    {"input": user_input},
                    {"output": full_response}
                )

        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            yield error_msg
            self.add_message("assistant", error_msg)

    def _demo_response(self, user_input: str) -> Generator[str, None, None]:
        """Generate a demo response when LangChain is not available"""
        import time

        demo_responses = {
            "sql": """Here's a SQL query to help you:

```sql
SELECT
    customer_id,
    customer_name,
    SUM(order_total) as total_revenue,
    COUNT(*) as order_count
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE order_date >= DATEADD(month, -12, CURRENT_DATE())
GROUP BY customer_id, customer_name
ORDER BY total_revenue DESC
LIMIT 10;
```

This query will:
1. Join orders with customers
2. Calculate total revenue per customer
3. Count orders per customer
4. Filter to last 12 months
5. Return top 10 by revenue""",

            "default": """I'm Cortex AI, your intelligent data assistant. I can help you with:

- **SQL Queries**: Write, optimize, and explain SQL for Snowflake, Databricks, and more
- **Data Analysis**: Explore patterns and generate insights from your data
- **Schema Design**: Help with data modeling and table structures
- **Query Optimization**: Improve performance of slow queries

How can I assist you today?"""
        }

        # Select response based on input
        if any(word in user_input.lower() for word in ['sql', 'query', 'select', 'table']):
            response = demo_responses["sql"]
        else:
            response = demo_responses["default"]

        # Simulate streaming
        for char in response:
            yield char
            time.sleep(0.005)

        self.add_message("assistant", response)


class SQLTool:
    """Tool for executing SQL queries (placeholder for Snowflake/Databricks integration)"""

    def __init__(self, connection_type: str = "snowflake"):
        self.connection_type = connection_type
        self.connection = None

    def connect(self, **kwargs):
        """Establish database connection"""
        # Placeholder - implement actual connection logic
        pass

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        # Placeholder - implement actual query execution
        return {
            "success": True,
            "data": [],
            "columns": [],
            "row_count": 0,
            "execution_time": 0.0
        }

    def get_schema(self, table_name: str = None) -> Dict[str, Any]:
        """Get database/table schema information"""
        # Placeholder
        return {
            "tables": [],
            "columns": {}
        }


def create_langchain_tools():
    """Create LangChain tools for the chatbot"""
    try:
        from langchain.tools import Tool

        tools = [
            Tool(
                name="execute_sql",
                func=lambda q: SQLTool().execute_query(q),
                description="Execute a SQL query against the connected database"
            ),
            Tool(
                name="get_schema",
                func=lambda t: SQLTool().get_schema(t),
                description="Get schema information for a table or the entire database"
            )
        ]
        return tools
    except ImportError:
        return []
