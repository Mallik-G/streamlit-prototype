"""
Application Configuration
Platform-aware settings for Snowflake or Databricks deployment
"""
import os
from enum import Enum
from typing import Optional
import json


class Platform(Enum):
    """Supported deployment platforms"""
    SNOWFLAKE = "snowflake"
    DATABRICKS = "databricks"
    LOCAL = "local"


class PlatformConfig:
    """Platform-specific configuration"""

    def __init__(self):
        self.config_file = "platform_config.json"
        self._platform = None
        self.load()

    def load(self):
        """Load platform configuration from file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                platform_str = data.get('platform', 'local')
                self._platform = Platform(platform_str)
        else:
            # Default to local if no config
            self._platform = Platform.LOCAL
            self.save()

    def save(self):
        """Save platform configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump({'platform': self._platform.value}, f)

    @property
    def platform(self) -> Platform:
        """Get current platform"""
        return self._platform

    @platform.setter
    def platform(self, value: Platform):
        """Set current platform"""
        self._platform = value
        self.save()

    def is_snowflake(self) -> bool:
        """Check if platform is Snowflake"""
        return self._platform == Platform.SNOWFLAKE

    def is_databricks(self) -> bool:
        """Check if platform is Databricks"""
        return self._platform == Platform.DATABRICKS

    def is_local(self) -> bool:
        """Check if platform is Local"""
        return self._platform == Platform.LOCAL

    def get_storage_label(self) -> str:
        """Get platform-specific storage label"""
        labels = {
            Platform.SNOWFLAKE: "Stage",
            Platform.DATABRICKS: "Volume",
            Platform.LOCAL: "Directory"
        }
        return labels[self._platform]

    def get_vector_search_label(self) -> str:
        """Get platform-specific vector search label"""
        labels = {
            Platform.SNOWFLAKE: "Cortex Search",
            Platform.DATABRICKS: "Vector Search",
            Platform.LOCAL: "ChromaDB"
        }
        return labels[self._platform]

    def get_embedding_options(self) -> list:
        """Get platform-specific embedding model options"""
        options = {
            Platform.SNOWFLAKE: [
                "snowflake-arctic-embed-m",
                "snowflake-arctic-embed-l",
                "e5-base-v2",
                "multilingual-e5-large"
            ],
            Platform.DATABRICKS: [
                "databricks-bge-large-en",
                "databricks-gte-large-en",
                "openai-text-embedding-ada-002"
            ],
            Platform.LOCAL: [
                "text-embedding-ada-002",
                "text-embedding-3-small",
                "text-embedding-3-large"
            ]
        }
        return options[self._platform]

    def get_model_providers(self) -> list:
        """Get available model providers for platform"""
        if self.is_databricks():
            return ["openai", "anthropic", "databricks"]
        elif self.is_snowflake():
            return ["openai", "anthropic", "snowflake"]
        else:
            return ["openai", "anthropic"]

    def get_database_options(self) -> list:
        """Get database/data source options"""
        if self.is_snowflake():
            return ["Snowflake"]
        elif self.is_databricks():
            return ["Databricks", "Unity Catalog"]
        else:
            return ["Demo Mode", "Local SQLite"]

    def get_platform_name(self) -> str:
        """Get display name for platform"""
        names = {
            Platform.SNOWFLAKE: "Snowflake",
            Platform.DATABRICKS: "Databricks",
            Platform.LOCAL: "Local Development"
        }
        return names[self._platform]

    def get_platform_icon(self) -> str:
        """Get icon for platform"""
        icons = {
            Platform.SNOWFLAKE: "❄️",
            Platform.DATABRICKS: "🧱",
            Platform.LOCAL: "💻"
        }
        return icons[self._platform]

    def get_platform_color(self) -> str:
        """Get brand color for platform"""
        colors = {
            Platform.SNOWFLAKE: "#29B5E8",
            Platform.DATABRICKS: "#FF3621",
            Platform.LOCAL: "#6B7D8F"
        }
        return colors[self._platform]

    def get_connection_fields(self) -> dict:
        """Get required connection fields for platform"""
        if self.is_snowflake():
            return {
                "account": "Snowflake Account",
                "user": "Username",
                "password": "Password",
                "warehouse": "Warehouse",
                "database": "Database",
                "schema": "Schema",
                "role": "Role (optional)"
            }
        elif self.is_databricks():
            return {
                "host": "Workspace URL",
                "http_path": "HTTP Path",
                "token": "Access Token",
                "catalog": "Catalog",
                "schema": "Schema"
            }
        else:
            return {}

    def validate_connection(self) -> tuple[bool, Optional[str]]:
        """Validate platform connection settings"""
        if self.is_snowflake():
            required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE"]
            missing = [f for f in required if not os.getenv(f)]
            if missing:
                return False, f"Missing Snowflake configuration: {', '.join(missing)}"
        elif self.is_databricks():
            required = ["DATABRICKS_HOST", "DATABRICKS_HTTP_PATH", "DATABRICKS_TOKEN"]
            missing = [f for f in required if not os.getenv(f)]
            if missing:
                return False, f"Missing Databricks configuration: {', '.join(missing)}"

        return True, None

    def get_quick_start_guide(self) -> str:
        """Get platform-specific quick start instructions"""
        guides = {
            Platform.SNOWFLAKE: """
### Snowflake Quick Start

1. **Set Environment Variables**:
```bash
export SNOWFLAKE_ACCOUNT="your_account"
export SNOWFLAKE_USER="your_user"
export SNOWFLAKE_PASSWORD="your_password"
export SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
export SNOWFLAKE_DATABASE="MY_DB"
export SNOWFLAKE_SCHEMA="PUBLIC"
```

2. **Create Stage for Documents**:
```sql
CREATE STAGE MY_DOCS_STAGE;
```

3. **Enable Cortex AI**:
```sql
-- Cortex is automatically available in most accounts
SELECT SNOWFLAKE.CORTEX.COMPLETE('llama2-70b-chat', 'Hello!');
```
""",
            Platform.DATABRICKS: """
### Databricks Quick Start

1. **Set Environment Variables**:
```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/abc123"
export DATABRICKS_TOKEN="dapi..."
export DATABRICKS_CATALOG="main"
export DATABRICKS_SCHEMA="default"
```

2. **Create Unity Catalog Volume**:
```sql
CREATE VOLUME main.default.my_docs;
```

3. **Setup Vector Search**:
```python
from databricks.vector_search.client import VectorSearchClient
client = VectorSearchClient()
client.create_endpoint("my_endpoint")
```
""",
            Platform.LOCAL: """
### Local Development Quick Start

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set OpenAI Key** (for embeddings):
```bash
export OPENAI_API_KEY="sk-..."
```

3. **Run the App**:
```bash
streamlit run app.py
```
"""
        }
        return guides[self._platform]


# Global configuration instance
_config = None


def get_platform_config() -> PlatformConfig:
    """Get global platform configuration"""
    global _config
    if _config is None:
        _config = PlatformConfig()
    return _config


def set_platform(platform: Platform):
    """Set global platform"""
    config = get_platform_config()
    config.platform = platform
