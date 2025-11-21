# Agent Builder Guide

## Overview

The Agent Builder provides a self-serve platform for creating, deploying, and sharing custom AI agents. Inspired by [Databricks Labs Kasal](https://github.com/databrickslabs/kasal), this system enables users to build specialized agents without writing code.

## Features

### 🔧 Agent Builder
- **Visual Configuration**: Create agents through an intuitive UI
- **Custom Prompts**: Define agent behavior and expertise
- **Model Selection**: Choose from OpenAI, Anthropic, or Databricks models
- **Tool Integration**: Add capabilities like SQL execution, web search, code interpretation
- **Memory Management**: Configure conversation memory types
- **Templates**: Start from pre-built agent templates

### 📚 Agent Templates
Pre-configured agents for common use cases:
- **Data Analyst**: Statistical analysis and insights
- **SQL Expert**: Query writing and optimization
- **Customer Support Agent**: Friendly support specialist
- **Content Writer**: Marketing and creative content
- **Python Developer**: Code development and debugging
- **Research Assistant**: Comprehensive research and synthesis
- **BI Analyst**: Business intelligence and KPIs
- **Databricks Expert**: Spark, Delta Lake, and MLflow
- **Snowflake Expert**: Data warehouse optimization

### 🏪 Agent Marketplace
- **Discover**: Browse public agents from the community
- **Filter & Search**: Find agents by category, tags, or name
- **Try Now**: Test agents before cloning
- **Clone & Customize**: Copy agents and modify for your needs
- **Publish**: Share your agents with others

## Getting Started

### Creating Your First Agent

1. **Navigate to Agent Builder** (🔧 in sidebar)

2. **Choose a Creation Method**:
   - **From Scratch**: Configure all settings manually
   - **From Template**: Start with a pre-built configuration

3. **Configure Basic Information**:
   ```
   Name: My Data Assistant
   Description: Helps analyze sales data and generate reports
   Category: Data Analysis
   Icon: 📊
   Tags: sales, analytics, reports
   ```

4. **Select Model**:
   - Provider: OpenAI / Anthropic / Databricks
   - Model: GPT-4, Claude 3, etc.
   - Temperature: 0.0 (precise) to 1.0 (creative)
   - Max Tokens: Response length limit

5. **Write System Prompt**:
   ```
   You are a sales data expert specializing in retail analytics.

   Your capabilities:
   - Analyze sales trends and patterns
   - Generate executive reports
   - Provide actionable recommendations

   Your approach:
   - Ask clarifying questions about the business context
   - Use data-driven insights
   - Present findings clearly
   ```

6. **Add Tools**:
   - ✓ SQL Executor - Run database queries
   - ✓ Data Visualizer - Create charts
   - ✓ Calculator - Perform calculations

7. **Advanced Settings**:
   - Enable Memory: Keep conversation context
   - Memory Type: Buffer / Summary / Window
   - Make Public: Share in marketplace

8. **Create Agent** 🚀

### Using an Agent

1. **From Agent Builder**:
   - Go to "My Agents" tab
   - Click "💬 Chat" on any agent

2. **From Main Chat**:
   - In sidebar, select agent from dropdown
   - Click "Load Agent"
   - Start chatting

3. **From Marketplace**:
   - Browse agents
   - Click "💬 Try Now"
   - Agent loads in chat interface

### Managing Agents

#### Edit Agent
- Click "📝 Edit" in My Agents
- Modify configuration
- Save changes

#### Publish Agent
- Click "🌐 Publish" to share publicly
- Agent appears in marketplace
- Others can clone and use it

#### Clone Agent
- Find agent in marketplace
- Click "📥 Clone"
- Customize for your needs

#### Delete Agent
- Click "🗑️ Delete" in My Agents
- Confirm deletion

## Agent Configuration Guide

### System Prompts

Good system prompts should:
- Define the agent's role and expertise
- List key capabilities
- Describe the communication style
- Include guidelines for behavior
- Specify what to prioritize

**Example - Technical Expert**:
```
You are a senior software engineer with expertise in Python and system design.

Your strengths:
- Writing clean, maintainable code
- Explaining complex concepts simply
- Debugging and troubleshooting
- Performance optimization

Your style:
- Concise and technical
- Provide code examples
- Explain tradeoffs
- Ask clarifying questions before proposing solutions
```

**Example - Business Analyst**:
```
You are a business analyst focused on data-driven decision making.

Your approach:
- Start by understanding business objectives
- Use data to support recommendations
- Present insights visually when appropriate
- Consider both quantitative and qualitative factors
- Highlight risks and assumptions

Communication:
- Use business terminology
- Avoid technical jargon
- Structure findings clearly
- Provide executive summaries
```

### Tool Selection

Choose tools based on agent purpose:

**Data Analysis Agents**:
- SQL Executor
- Data Visualizer
- Calculator

**Development Agents**:
- Code Interpreter
- File Reader
- API Caller

**Research Agents**:
- Web Search
- File Reader
- API Caller

**Customer Support**:
- Web Search (for KB articles)
- API Caller (for ticketing systems)

### Model Selection

**OpenAI**:
- GPT-4: Best reasoning, complex tasks
- GPT-4-Turbo: Faster, cost-effective
- GPT-3.5-Turbo: Quick, simple tasks

**Anthropic**:
- Claude 3 Opus: Highest capability
- Claude 3 Sonnet: Balanced performance
- Claude 3 Haiku: Fast, efficient

**Databricks**:
- DBRX Instruct: General purpose
- Llama 3 70B: Open source option

### Temperature Settings

- **0.0 - 0.3**: Deterministic, precise (SQL, code, data analysis)
- **0.4 - 0.7**: Balanced (general assistant, support)
- **0.8 - 1.0**: Creative (content writing, brainstorming)

## Architecture

### Storage
Agents are stored as JSON files in the `agents/` directory:
```json
{
  "id": "abc123",
  "name": "Data Analyst",
  "description": "Expert at analyzing datasets",
  "system_prompt": "You are a data analyst...",
  "model_provider": "openai",
  "model_name": "gpt-4",
  "temperature": 0.3,
  "tools": [
    {"name": "sql_executor", "enabled": true}
  ],
  "is_public": true,
  "category": "Data Analysis",
  "tags": ["analytics", "data"]
}
```

### Components

- **agent_builder.py**: Core agent management
- **agent_templates.py**: Pre-built templates
- **pages/1_🔧_Agent_Builder.py**: Builder UI
- **pages/2_🏪_Agent_Marketplace.py**: Marketplace UI
- **app.py**: Main chat interface with agent support

### Execution Flow

1. User selects/loads agent
2. AgentExecutor initializes with config
3. ChatEngine created with agent settings
4. User input processed through agent
5. Response streamed back to UI

## API Reference

### AgentBuilder

```python
from agent_builder import AgentBuilder

builder = AgentBuilder()

# Create agent
agent = builder.create_agent(
    name="My Agent",
    description="Description",
    system_prompt="You are...",
    model_provider="openai",
    model_name="gpt-4",
    temperature=0.7
)

# Load agent
agent = builder.load_agent(agent_id)

# List agents
agents = builder.list_agents(
    creator="user@example.com",
    category="Data Analysis",
    public_only=True
)

# Publish agent
builder.publish_agent(agent_id)
```

### AgentExecutor

```python
from agent_builder import AgentExecutor

executor = AgentExecutor(agent_config)

# Execute and stream response
for chunk in executor.execute("What's the sales trend?"):
    print(chunk, end="")

# Get history
messages = executor.get_conversation_history()
```

## Comparison with Kasal

| Feature | Cortex AI Agent Builder | Kasal |
|---------|------------------------|-------|
| Visual Builder | ✓ Form-based | ✓ Drag-and-drop canvas |
| Templates | ✓ 9 pre-built | ✓ Crew templates |
| Marketplace | ✓ Share & discover | ✗ Not mentioned |
| Multi-agent | ✗ Single agent | ✓ CrewAI orchestration |
| Tools | ✓ 7 built-in | ✓ Genie, custom APIs |
| Monitoring | Basic | ✓ MLFlow integration |
| Platform | Streamlit | React + FastAPI |
| Database | JSON files | Database backend |

## Best Practices

### Agent Design
1. **Single Responsibility**: Each agent should have a clear, focused purpose
2. **Clear Prompts**: Be explicit about capabilities and limitations
3. **Tool Selection**: Only include necessary tools
4. **Test Thoroughly**: Try various inputs before publishing
5. **Iterate**: Refine based on usage patterns

### Security
- Don't include API keys in prompts
- Review public agents before use
- Test cloned agents in private mode first
- Set appropriate memory settings for sensitive data

### Performance
- Use appropriate models (don't use GPT-4 for simple tasks)
- Set reasonable token limits
- Use lower temperatures for deterministic tasks
- Clear history periodically for long conversations

## Troubleshooting

**Agent not appearing in marketplace**:
- Ensure "Make Public" is enabled
- Check agent is saved correctly

**Agent responses incorrect**:
- Review system prompt
- Check model selection
- Adjust temperature
- Verify tools are configured

**Can't load agent**:
- Check agent ID is correct
- Verify agent file exists in `agents/` directory
- Check JSON format is valid

## Roadmap

Planned features:
- [ ] Multi-agent workflows (like Kasal)
- [ ] Visual workflow designer
- [ ] Agent analytics and monitoring
- [ ] Version control for agents
- [ ] Agent testing sandbox
- [ ] Import/export agents
- [ ] Agent ratings and reviews
- [ ] Scheduled agent execution
- [ ] Webhook integrations
- [ ] Human-in-the-loop approval

## Contributing

To add new features:
1. Add tools in `get_available_tools()`
2. Create templates in `agent_templates.py`
3. Extend UI in agent builder pages
4. Update this guide

## Support

For issues or questions:
- Check existing agents for examples
- Review agent templates
- Test in demo mode first
- Share feedback on successful patterns
