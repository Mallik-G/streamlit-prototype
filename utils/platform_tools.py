"""
Platform-Native Tools Registry
Discover and use tools registered in Unity Catalog (Databricks) or Snowflake UDFs
Security-focused: Only use pre-approved, platform-registered functions
"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json


@dataclass
class PlatformTool:
    """Represents a platform-registered tool/function"""
    id: str
    name: str
    description: str
    catalog: str  # Catalog name (Databricks) or Database (Snowflake)
    schema: str
    function_name: str
    input_params: List[Dict[str, str]]
    return_type: str
    platform: str  # 'databricks' or 'snowflake'
    function_type: str  # 'sql', 'python', 'scalar', 'table', 'procedure'
    example_usage: Optional[str] = None


class DatabricksToolRegistry:
    """Discover and manage tools from Unity Catalog"""

    def __init__(self):
        self.catalog = os.getenv("DATABRICKS_CATALOG", "main")
        self.connection = None

    def connect(self):
        """Connect to Databricks"""
        try:
            from databricks import sql

            self.connection = sql.connect(
                server_hostname=os.getenv("DATABRICKS_HOST"),
                http_path=os.getenv("DATABRICKS_HTTP_PATH"),
                access_token=os.getenv("DATABRICKS_TOKEN")
            )
            return True
        except Exception as e:
            print(f"Databricks connection error: {e}")
            return False

    def discover_functions(self, schema: str = None) -> List[PlatformTool]:
        """Discover registered functions in Unity Catalog"""
        if not self.connection:
            if not self.connect():
                return []

        functions = []
        schema_filter = f"AND function_schema = '{schema}'" if schema else ""

        try:
            cursor = self.connection.cursor()

            # Query UC functions
            query = f"""
                SELECT
                    function_catalog,
                    function_schema,
                    function_name,
                    data_type as return_type,
                    comment,
                    routine_definition
                FROM system.information_schema.routines
                WHERE function_catalog = '{self.catalog}'
                {schema_filter}
                AND routine_type IN ('FUNCTION', 'PROCEDURE')
                ORDER BY function_schema, function_name
            """

            cursor.execute(query)
            results = cursor.fetchall()

            for row in results:
                catalog, schema, func_name, return_type, comment, definition = row

                # Parse input parameters from definition
                params = self._parse_parameters(definition)

                tool = PlatformTool(
                    id=f"{catalog}.{schema}.{func_name}",
                    name=func_name,
                    description=comment or f"UC Function: {func_name}",
                    catalog=catalog,
                    schema=schema,
                    function_name=func_name,
                    input_params=params,
                    return_type=return_type or "STRING",
                    platform="databricks",
                    function_type="sql",
                    example_usage=f"SELECT {catalog}.{schema}.{func_name}(...)"
                )
                functions.append(tool)

            cursor.close()
            return functions

        except Exception as e:
            print(f"Error discovering UC functions: {e}")
            return []

    def get_metric_views(self) -> List[Dict[str, Any]]:
        """Get available metric views from Unity Catalog"""
        if not self.connection:
            if not self.connect():
                return []

        try:
            cursor = self.connection.cursor()

            query = f"""
                SELECT
                    table_catalog,
                    table_schema,
                    table_name,
                    table_type,
                    comment
                FROM system.information_schema.tables
                WHERE table_catalog = '{self.catalog}'
                AND table_type = 'VIEW'
                AND table_name LIKE '%metric%'
                ORDER BY table_schema, table_name
            """

            cursor.execute(query)
            results = cursor.fetchall()

            metric_views = []
            for row in results:
                catalog, schema, name, table_type, comment = row
                metric_views.append({
                    "catalog": catalog,
                    "schema": schema,
                    "name": name,
                    "type": table_type,
                    "description": comment or f"Metric view: {name}",
                    "full_name": f"{catalog}.{schema}.{name}"
                })

            cursor.close()
            return metric_views

        except Exception as e:
            print(f"Error getting metric views: {e}")
            return []

    def execute_function(self, tool: PlatformTool, params: Dict[str, Any]) -> Any:
        """Execute a Unity Catalog function"""
        if not self.connection:
            if not self.connect():
                return None

        try:
            cursor = self.connection.cursor()

            # Build function call
            param_values = [params.get(p['name'], 'NULL') for p in tool.input_params]
            param_str = ', '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in param_values])

            query = f"SELECT {tool.catalog}.{tool.schema}.{tool.function_name}({param_str})"

            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()

            return result[0] if result else None

        except Exception as e:
            print(f"Error executing UC function: {e}")
            return None

    def _parse_parameters(self, definition: str) -> List[Dict[str, str]]:
        """Parse function parameters from definition"""
        # Simplified parameter parsing
        # In production, use proper SQL parsing
        params = []

        if not definition:
            return params

        # Extract parameters between first ( and )
        try:
            start = definition.index('(')
            end = definition.index(')', start)
            param_str = definition[start + 1:end].strip()

            if param_str:
                for param in param_str.split(','):
                    parts = param.strip().split()
                    if len(parts) >= 2:
                        params.append({
                            "name": parts[0],
                            "type": parts[1]
                        })
        except:
            pass

        return params

    def close(self):
        """Close connection"""
        if self.connection:
            self.connection.close()


class SnowflakeToolRegistry:
    """Discover and manage tools from Snowflake UDFs and Stored Procedures"""

    def __init__(self):
        self.database = os.getenv("SNOWFLAKE_DATABASE", "")
        self.session = None

    def connect(self):
        """Connect to Snowflake"""
        try:
            from snowflake.snowpark import Session

            connection_parameters = {
                "account": os.getenv("SNOWFLAKE_ACCOUNT"),
                "user": os.getenv("SNOWFLAKE_USER"),
                "password": os.getenv("SNOWFLAKE_PASSWORD"),
                "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
                "database": os.getenv("SNOWFLAKE_DATABASE"),
                "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
            }

            role = os.getenv("SNOWFLAKE_ROLE")
            if role:
                connection_parameters["role"] = role

            self.session = Session.builder.configs(connection_parameters).create()
            return True

        except Exception as e:
            print(f"Snowflake connection error: {e}")
            return False

    def discover_functions(self, schema: str = None) -> List[PlatformTool]:
        """Discover UDFs and stored procedures in Snowflake"""
        if not self.session:
            if not self.connect():
                return []

        functions = []
        schema_filter = f"AND FUNCTION_SCHEMA = '{schema}'" if schema else ""

        try:
            query = f"""
                SELECT
                    FUNCTION_CATALOG,
                    FUNCTION_SCHEMA,
                    FUNCTION_NAME,
                    DATA_TYPE as RETURN_TYPE,
                    COMMENT,
                    ARGUMENT_SIGNATURE,
                    FUNCTION_LANGUAGE
                FROM {self.database}.INFORMATION_SCHEMA.FUNCTIONS
                WHERE FUNCTION_CATALOG = '{self.database}'
                {schema_filter}
                ORDER BY FUNCTION_SCHEMA, FUNCTION_NAME
            """

            result = self.session.sql(query).to_pandas()

            for _, row in result.iterrows():
                # Parse parameters
                params = self._parse_signature(row['ARGUMENT_SIGNATURE'])

                tool = PlatformTool(
                    id=f"{row['FUNCTION_CATALOG']}.{row['FUNCTION_SCHEMA']}.{row['FUNCTION_NAME']}",
                    name=row['FUNCTION_NAME'],
                    description=row['COMMENT'] or f"Snowflake UDF: {row['FUNCTION_NAME']}",
                    catalog=row['FUNCTION_CATALOG'],
                    schema=row['FUNCTION_SCHEMA'],
                    function_name=row['FUNCTION_NAME'],
                    input_params=params,
                    return_type=row['RETURN_TYPE'] or "VARCHAR",
                    platform="snowflake",
                    function_type=row['FUNCTION_LANGUAGE'].lower() if row['FUNCTION_LANGUAGE'] else "sql",
                    example_usage=f"SELECT {row['FUNCTION_CATALOG']}.{row['FUNCTION_SCHEMA']}.{row['FUNCTION_NAME']}(...)"
                )
                functions.append(tool)

            return functions

        except Exception as e:
            print(f"Error discovering Snowflake functions: {e}")
            return []

    def get_semantic_models(self) -> List[Dict[str, Any]]:
        """Get Snowflake semantic layer models"""
        if not self.session:
            if not self.connect():
                return []

        try:
            # Query semantic models (views tagged with semantic metadata)
            query = f"""
                SELECT
                    TABLE_CATALOG,
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    TABLE_TYPE,
                    COMMENT
                FROM {self.database}.INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'VIEW'
                AND (
                    COMMENT LIKE '%metric%'
                    OR COMMENT LIKE '%semantic%'
                    OR TABLE_NAME LIKE '%_METRIC%'
                )
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """

            result = self.session.sql(query).to_pandas()

            models = []
            for _, row in result.iterrows():
                models.append({
                    "database": row['TABLE_CATALOG'],
                    "schema": row['TABLE_SCHEMA'],
                    "name": row['TABLE_NAME'],
                    "type": row['TABLE_TYPE'],
                    "description": row['COMMENT'] or f"Semantic model: {row['TABLE_NAME']}",
                    "full_name": f"{row['TABLE_CATALOG']}.{row['TABLE_SCHEMA']}.{row['TABLE_NAME']}"
                })

            return models

        except Exception as e:
            print(f"Error getting semantic models: {e}")
            return []

    def execute_function(self, tool: PlatformTool, params: Dict[str, Any]) -> Any:
        """Execute a Snowflake UDF"""
        if not self.session:
            if not self.connect():
                return None

        try:
            # Build function call
            param_values = [params.get(p['name'], 'NULL') for p in tool.input_params]
            param_str = ', '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in param_values])

            query = f"SELECT {tool.catalog}.{tool.schema}.{tool.function_name}({param_str})"

            result = self.session.sql(query).collect()

            return result[0][0] if result else None

        except Exception as e:
            print(f"Error executing Snowflake function: {e}")
            return None

    def _parse_signature(self, signature: str) -> List[Dict[str, str]]:
        """Parse function signature for parameters"""
        params = []

        if not signature:
            return params

        # Parse "(param1 TYPE1, param2 TYPE2)" format
        try:
            signature = signature.strip()
            if signature.startswith('(') and signature.endswith(')'):
                signature = signature[1:-1]

            for param in signature.split(','):
                parts = param.strip().split()
                if len(parts) >= 2:
                    params.append({
                        "name": parts[0],
                        "type": ' '.join(parts[1:])
                    })
        except:
            pass

        return params

    def close(self):
        """Close connection"""
        if self.session:
            self.session.close()


class PlatformToolManager:
    """Unified manager for platform-native tools"""

    def __init__(self, platform: str):
        self.platform = platform.lower()
        self.registry = None

        if self.platform == "databricks":
            self.registry = DatabricksToolRegistry()
        elif self.platform == "snowflake":
            self.registry = SnowflakeToolRegistry()

    def discover_all_tools(self) -> List[PlatformTool]:
        """Discover all available platform tools"""
        if not self.registry:
            return []

        return self.registry.discover_functions()

    def get_tool(self, tool_id: str) -> Optional[PlatformTool]:
        """Get specific tool by ID"""
        tools = self.discover_all_tools()
        for tool in tools:
            if tool.id == tool_id:
                return tool
        return None

    def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> Any:
        """Execute a platform tool"""
        tool = self.get_tool(tool_id)
        if not tool:
            return None

        return self.registry.execute_function(tool, params)

    def get_metrics(self) -> List[Dict[str, Any]]:
        """Get available metrics/semantic models"""
        if not self.registry:
            return []

        if self.platform == "databricks":
            return self.registry.get_metric_views()
        elif self.platform == "snowflake":
            return self.registry.get_semantic_models()

        return []

    def query_metric(self, metric_name: str, filters: Dict[str, Any] = None) -> Any:
        """Query a metric view with optional filters"""
        if not self.registry or not self.registry.connection and not self.registry.session:
            return None

        try:
            # Build WHERE clause from filters
            where_clause = ""
            if filters:
                conditions = [f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}"
                             for k, v in filters.items()]
                where_clause = " WHERE " + " AND ".join(conditions)

            query = f"SELECT * FROM {metric_name}{where_clause}"

            if self.platform == "databricks":
                cursor = self.registry.connection.cursor()
                cursor.execute(query)
                result = cursor.fetchall()
                cursor.close()
                return result
            elif self.platform == "snowflake":
                result = self.registry.session.sql(query).to_pandas()
                return result

        except Exception as e:
            print(f"Error querying metric: {e}")
            return None

    def save_tool_registry(self, filepath: str = "platform_tools.json"):
        """Save discovered tools to file for caching"""
        tools = self.discover_all_tools()
        metrics = self.get_metrics()

        data = {
            "platform": self.platform,
            "tools": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "catalog": t.catalog,
                    "schema": t.schema,
                    "function_name": t.function_name,
                    "input_params": t.input_params,
                    "return_type": t.return_type,
                    "function_type": t.function_type,
                    "example_usage": t.example_usage
                }
                for t in tools
            ],
            "metrics": metrics
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_tool_registry(self, filepath: str = "platform_tools.json") -> List[PlatformTool]:
        """Load tools from cached file"""
        if not os.path.exists(filepath):
            return []

        with open(filepath, 'r') as f:
            data = json.load(f)

        tools = []
        for t in data.get('tools', []):
            tool = PlatformTool(
                id=t['id'],
                name=t['name'],
                description=t['description'],
                catalog=t['catalog'],
                schema=t['schema'],
                function_name=t['function_name'],
                input_params=t['input_params'],
                return_type=t['return_type'],
                platform=self.platform,
                function_type=t['function_type'],
                example_usage=t.get('example_usage')
            )
            tools.append(tool)

        return tools


def get_platform_tools(platform: str) -> PlatformToolManager:
    """Factory function to get platform tool manager"""
    return PlatformToolManager(platform)
