"""
Data Connectors - Snowflake and Databricks Integration
"""
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import pandas as pd


@dataclass
class QueryResult:
    """Data class for query results"""
    success: bool
    data: pd.DataFrame
    columns: List[str]
    row_count: int
    execution_time: float
    error: Optional[str] = None


class SnowflakeConnector:
    """Snowflake database connector using Snowpark"""

    def __init__(
        self,
        account: str = None,
        user: str = None,
        password: str = None,
        warehouse: str = None,
        database: str = None,
        schema: str = None,
        role: str = None
    ):
        self.account = account or os.getenv("SNOWFLAKE_ACCOUNT")
        self.user = user or os.getenv("SNOWFLAKE_USER")
        self.password = password or os.getenv("SNOWFLAKE_PASSWORD")
        self.warehouse = warehouse or os.getenv("SNOWFLAKE_WAREHOUSE")
        self.database = database or os.getenv("SNOWFLAKE_DATABASE")
        self.schema = schema or os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
        self.role = role or os.getenv("SNOWFLAKE_ROLE")
        self.session = None

    def connect(self) -> bool:
        """Establish connection to Snowflake using Snowpark"""
        try:
            from snowflake.snowpark import Session

            connection_parameters = {
                "account": self.account,
                "user": self.user,
                "password": self.password,
                "warehouse": self.warehouse,
                "database": self.database,
                "schema": self.schema,
            }
            if self.role:
                connection_parameters["role"] = self.role

            self.session = Session.builder.configs(connection_parameters).create()
            return True

        except ImportError:
            print("Snowpark not installed. Install with: pip install snowflake-snowpark-python")
            return False
        except Exception as e:
            print(f"Snowflake connection error: {e}")
            return False

    def execute_query(self, query: str) -> QueryResult:
        """Execute a SQL query and return results"""
        import time

        if not self.session:
            return QueryResult(
                success=False,
                data=pd.DataFrame(),
                columns=[],
                row_count=0,
                execution_time=0.0,
                error="Not connected to Snowflake"
            )

        try:
            start_time = time.time()
            result = self.session.sql(query).to_pandas()
            execution_time = time.time() - start_time

            return QueryResult(
                success=True,
                data=result,
                columns=list(result.columns),
                row_count=len(result),
                execution_time=execution_time
            )

        except Exception as e:
            return QueryResult(
                success=False,
                data=pd.DataFrame(),
                columns=[],
                row_count=0,
                execution_time=0.0,
                error=str(e)
            )

    def get_tables(self) -> List[Dict[str, str]]:
        """Get list of tables in current schema"""
        if not self.session:
            return []

        try:
            query = """
                SELECT TABLE_NAME, TABLE_TYPE, ROW_COUNT, BYTES
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
                ORDER BY TABLE_NAME
            """
            result = self.session.sql(query).to_pandas()
            return result.to_dict('records')
        except Exception:
            return []

    def get_columns(self, table_name: str) -> List[Dict[str, str]]:
        """Get columns for a specific table"""
        if not self.session:
            return []

        try:
            query = f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table_name}'
                AND TABLE_SCHEMA = CURRENT_SCHEMA()
                ORDER BY ORDINAL_POSITION
            """
            result = self.session.sql(query).to_pandas()
            return result.to_dict('records')
        except Exception:
            return []

    def close(self):
        """Close the Snowflake session"""
        if self.session:
            self.session.close()
            self.session = None


class DatabricksConnector:
    """Databricks SQL connector"""

    def __init__(
        self,
        server_hostname: str = None,
        http_path: str = None,
        access_token: str = None,
        catalog: str = None,
        schema: str = None
    ):
        self.server_hostname = server_hostname or os.getenv("DATABRICKS_HOST")
        self.http_path = http_path or os.getenv("DATABRICKS_HTTP_PATH")
        self.access_token = access_token or os.getenv("DATABRICKS_TOKEN")
        self.catalog = catalog or os.getenv("DATABRICKS_CATALOG", "main")
        self.schema = schema or os.getenv("DATABRICKS_SCHEMA", "default")
        self.connection = None
        self.cursor = None

    def connect(self) -> bool:
        """Establish connection to Databricks SQL"""
        try:
            from databricks import sql

            self.connection = sql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                access_token=self.access_token,
                catalog=self.catalog,
                schema=self.schema
            )
            self.cursor = self.connection.cursor()
            return True

        except ImportError:
            print("Databricks SQL connector not installed. Install with: pip install databricks-sql-connector")
            return False
        except Exception as e:
            print(f"Databricks connection error: {e}")
            return False

    def execute_query(self, query: str) -> QueryResult:
        """Execute a SQL query and return results"""
        import time

        if not self.cursor:
            return QueryResult(
                success=False,
                data=pd.DataFrame(),
                columns=[],
                row_count=0,
                execution_time=0.0,
                error="Not connected to Databricks"
            )

        try:
            start_time = time.time()
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            execution_time = time.time() - start_time

            df = pd.DataFrame(results, columns=columns)

            return QueryResult(
                success=True,
                data=df,
                columns=columns,
                row_count=len(df),
                execution_time=execution_time
            )

        except Exception as e:
            return QueryResult(
                success=False,
                data=pd.DataFrame(),
                columns=[],
                row_count=0,
                execution_time=0.0,
                error=str(e)
            )

    def get_tables(self) -> List[Dict[str, str]]:
        """Get list of tables in current catalog/schema"""
        if not self.cursor:
            return []

        try:
            query = f"SHOW TABLES IN {self.catalog}.{self.schema}"
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return [{"table_name": row[1], "database": row[0]} for row in results]
        except Exception:
            return []

    def get_columns(self, table_name: str) -> List[Dict[str, str]]:
        """Get columns for a specific table"""
        if not self.cursor:
            return []

        try:
            query = f"DESCRIBE TABLE {self.catalog}.{self.schema}.{table_name}"
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            return [
                {"column_name": row[0], "data_type": row[1], "comment": row[2]}
                for row in results
            ]
        except Exception:
            return []

    def close(self):
        """Close the Databricks connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.cursor = None
        self.connection = None


class MockConnector:
    """Mock connector for demo/development without real database"""

    def __init__(self):
        self.connected = False

    def connect(self) -> bool:
        self.connected = True
        return True

    def execute_query(self, query: str) -> QueryResult:
        """Return sample data for demo purposes"""
        import time
        import random

        time.sleep(0.5)  # Simulate query time

        # Generate sample data based on query keywords
        if "customer" in query.lower():
            data = pd.DataFrame({
                "customer_id": range(1, 11),
                "customer_name": [f"Customer {i}" for i in range(1, 11)],
                "total_revenue": [random.randint(10000, 100000) for _ in range(10)],
                "order_count": [random.randint(5, 50) for _ in range(10)]
            })
        elif "sales" in query.lower() or "order" in query.lower():
            data = pd.DataFrame({
                "order_date": pd.date_range(start="2024-01-01", periods=10, freq="M"),
                "total_sales": [random.randint(50000, 200000) for _ in range(10)],
                "order_count": [random.randint(100, 500) for _ in range(10)],
                "avg_order_value": [random.randint(100, 500) for _ in range(10)]
            })
        else:
            data = pd.DataFrame({
                "id": range(1, 6),
                "name": ["Item A", "Item B", "Item C", "Item D", "Item E"],
                "value": [100, 200, 150, 300, 250],
                "status": ["Active", "Active", "Inactive", "Active", "Active"]
            })

        return QueryResult(
            success=True,
            data=data,
            columns=list(data.columns),
            row_count=len(data),
            execution_time=0.5
        )

    def get_tables(self) -> List[Dict[str, str]]:
        return [
            {"TABLE_NAME": "customers", "TABLE_TYPE": "TABLE", "ROW_COUNT": 10000},
            {"TABLE_NAME": "orders", "TABLE_TYPE": "TABLE", "ROW_COUNT": 50000},
            {"TABLE_NAME": "products", "TABLE_TYPE": "TABLE", "ROW_COUNT": 500},
            {"TABLE_NAME": "sales_summary", "TABLE_TYPE": "VIEW", "ROW_COUNT": None},
        ]

    def get_columns(self, table_name: str) -> List[Dict[str, str]]:
        schemas = {
            "customers": [
                {"COLUMN_NAME": "customer_id", "DATA_TYPE": "INTEGER"},
                {"COLUMN_NAME": "customer_name", "DATA_TYPE": "VARCHAR"},
                {"COLUMN_NAME": "email", "DATA_TYPE": "VARCHAR"},
                {"COLUMN_NAME": "created_at", "DATA_TYPE": "TIMESTAMP"},
            ],
            "orders": [
                {"COLUMN_NAME": "order_id", "DATA_TYPE": "INTEGER"},
                {"COLUMN_NAME": "customer_id", "DATA_TYPE": "INTEGER"},
                {"COLUMN_NAME": "order_date", "DATA_TYPE": "DATE"},
                {"COLUMN_NAME": "total_amount", "DATA_TYPE": "DECIMAL"},
            ],
        }
        return schemas.get(table_name, [])

    def close(self):
        self.connected = False


def get_connector(connector_type: str = "mock", **kwargs):
    """Factory function to get the appropriate connector"""
    connectors = {
        "snowflake": SnowflakeConnector,
        "databricks": DatabricksConnector,
        "mock": MockConnector
    }

    connector_class = connectors.get(connector_type.lower(), MockConnector)
    return connector_class(**kwargs)
