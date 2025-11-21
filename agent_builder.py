"""
Agent Builder Module - Self-serve Agent Creation and Management
Inspired by Databricks Labs Kasal
"""
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid


@dataclass
class AgentTool:
    """Configuration for an agent tool"""
    name: str
    description: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Complete agent configuration"""
    id: str
    name: str
    description: str
    system_prompt: str
    model_provider: str
    model_name: str
    temperature: float
    max_tokens: int
    enable_memory: bool
    memory_type: str
    tools: List[AgentTool]
    tags: List[str]
    creator: str
    created_at: str
    updated_at: str
    is_public: bool
    version: str
    category: str
    icon: str = "🤖"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create from dictionary"""
        tools = [AgentTool(**tool) if isinstance(tool, dict) else tool for tool in data.get('tools', [])]
        data['tools'] = tools
        return cls(**data)


class AgentBuilder:
    """Agent builder for creating and managing custom agents"""

    def __init__(self, storage_path: str = "agents"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def create_agent(
        self,
        name: str,
        description: str,
        system_prompt: str,
        model_provider: str = "openai",
        model_name: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        enable_memory: bool = True,
        memory_type: str = "buffer",
        tools: List[AgentTool] = None,
        tags: List[str] = None,
        creator: str = "anonymous",
        category: str = "general",
        is_public: bool = False,
        icon: str = "🤖"
    ) -> AgentConfig:
        """Create a new agent configuration"""
        agent_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        agent = AgentConfig(
            id=agent_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            model_provider=model_provider,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_memory=enable_memory,
            memory_type=memory_type,
            tools=tools or [],
            tags=tags or [],
            creator=creator,
            created_at=now,
            updated_at=now,
            is_public=is_public,
            version="1.0.0",
            category=category,
            icon=icon
        )

        self.save_agent(agent)
        return agent

    def save_agent(self, agent: AgentConfig):
        """Save agent configuration to disk"""
        file_path = os.path.join(self.storage_path, f"{agent.id}.json")
        with open(file_path, 'w') as f:
            json.dump(agent.to_dict(), f, indent=2)

    def load_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Load agent configuration by ID"""
        file_path = os.path.join(self.storage_path, f"{agent_id}.json")
        if not os.path.exists(file_path):
            return None

        with open(file_path, 'r') as f:
            data = json.load(f)
            return AgentConfig.from_dict(data)

    def update_agent(self, agent: AgentConfig):
        """Update existing agent configuration"""
        agent.updated_at = datetime.now().isoformat()
        self.save_agent(agent)

    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent configuration"""
        file_path = os.path.join(self.storage_path, f"{agent_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def list_agents(
        self,
        creator: str = None,
        category: str = None,
        tags: List[str] = None,
        public_only: bool = False
    ) -> List[AgentConfig]:
        """List all agents with optional filters"""
        agents = []

        for filename in os.listdir(self.storage_path):
            if not filename.endswith('.json'):
                continue

            with open(os.path.join(self.storage_path, filename), 'r') as f:
                data = json.load(f)
                agent = AgentConfig.from_dict(data)

                # Apply filters
                if public_only and not agent.is_public:
                    continue
                if creator and agent.creator != creator:
                    continue
                if category and agent.category != category:
                    continue
                if tags and not any(tag in agent.tags for tag in tags):
                    continue

                agents.append(agent)

        # Sort by updated_at descending
        agents.sort(key=lambda x: x.updated_at, reverse=True)
        return agents

    def duplicate_agent(self, agent_id: str, new_name: str, creator: str) -> Optional[AgentConfig]:
        """Duplicate an existing agent"""
        original = self.load_agent(agent_id)
        if not original:
            return None

        return self.create_agent(
            name=new_name,
            description=original.description,
            system_prompt=original.system_prompt,
            model_provider=original.model_provider,
            model_name=original.model_name,
            temperature=original.temperature,
            max_tokens=original.max_tokens,
            enable_memory=original.enable_memory,
            memory_type=original.memory_type,
            tools=original.tools.copy(),
            tags=original.tags.copy(),
            creator=creator,
            category=original.category,
            is_public=False,
            icon=original.icon
        )

    def publish_agent(self, agent_id: str) -> bool:
        """Publish agent to marketplace"""
        agent = self.load_agent(agent_id)
        if not agent:
            return False

        agent.is_public = True
        self.update_agent(agent)
        return True

    def unpublish_agent(self, agent_id: str) -> bool:
        """Unpublish agent from marketplace"""
        agent = self.load_agent(agent_id)
        if not agent:
            return False

        agent.is_public = False
        self.update_agent(agent)
        return True


class AgentExecutor:
    """Execute configured agents"""

    def __init__(self, agent_config: AgentConfig):
        self.config = agent_config
        self.chat_engine = None
        self._initialize_engine()

    def _initialize_engine(self):
        """Initialize chat engine from agent config"""
        from chat import ChatEngine

        self.chat_engine = ChatEngine(
            model_name=self.config.model_name,
            provider=self.config.model_provider,
            temperature=self.config.temperature,
            system_prompt=self.config.system_prompt,
            enable_memory=self.config.enable_memory
        )

    def execute(self, user_input: str):
        """Execute agent with user input"""
        if not self.chat_engine:
            self._initialize_engine()

        return self.chat_engine.generate_response(user_input)

    def get_conversation_history(self):
        """Get conversation history"""
        return self.chat_engine.get_messages()

    def clear_history(self):
        """Clear conversation history"""
        self.chat_engine.clear_history()


def get_available_tools() -> List[Dict[str, Any]]:
    """Get list of available tools for agent configuration"""
    return [
        {
            "id": "sql_executor",
            "name": "SQL Executor",
            "description": "Execute SQL queries against connected databases",
            "icon": "💾",
            "category": "data"
        },
        {
            "id": "web_search",
            "name": "Web Search",
            "description": "Search the web for current information",
            "icon": "🔍",
            "category": "search"
        },
        {
            "id": "calculator",
            "name": "Calculator",
            "description": "Perform mathematical calculations",
            "icon": "🧮",
            "category": "utility"
        },
        {
            "id": "code_interpreter",
            "name": "Code Interpreter",
            "description": "Execute Python code safely",
            "icon": "🐍",
            "category": "code"
        },
        {
            "id": "file_reader",
            "name": "File Reader",
            "description": "Read and analyze files",
            "icon": "📄",
            "category": "data"
        },
        {
            "id": "data_visualizer",
            "name": "Data Visualizer",
            "description": "Create charts and visualizations",
            "icon": "📊",
            "category": "visualization"
        },
        {
            "id": "api_caller",
            "name": "API Caller",
            "description": "Make HTTP requests to external APIs",
            "icon": "🌐",
            "category": "integration"
        }
    ]


def get_model_options() -> Dict[str, List[str]]:
    """Get available model options by provider"""
    return {
        "openai": [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-3.5-turbo"
        ],
        "anthropic": [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022"
        ],
        "databricks": [
            "databricks-dbrx-instruct",
            "databricks-meta-llama-3-70b-instruct"
        ]
    }
