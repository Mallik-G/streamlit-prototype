"""
Domain Discovery Engine

Automatically discovers tables, metrics, and functions based on domain tags
in Unity Catalog (Databricks) or Snowflake Information Schema.

Usage:
    # Discover finance domain resources
    discovery = DomainDiscoveryEngine(platform_config)
    resources = discovery.discover_domain("finance")

    # Auto-configure agent
    agent = discovery.create_domain_agent(
        domain="finance",
        business_unit="finance_bu",
        role="analyst"
    )
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
import json
from datetime import datetime, timedelta

from config import PlatformConfig
from utils.data_connectors import SnowflakeConnector, DatabricksConnector
from utils.logging_config import get_logger, get_performance_logger

logger = get_logger("domain_discovery")
perf_logger = get_performance_logger()


@dataclass
class DomainResource:
    """A discovered domain resource (table, metric, function)"""
    name: str
    type: str  # table, view, metric, function
    domain: str
    business_unit: Optional[str] = None
    description: Optional[str] = None
    schema: Optional[str] = None
    catalog: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    columns: List[Dict[str, Any]] = field(default_factory=list)
    sample_queries: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    last_updated: Optional[str] = None
    owner: Optional[str] = None


@dataclass
class DomainProfile:
    """Complete profile of discovered domain resources"""
    domain: str
    business_unit: Optional[str]
    tables: List[DomainResource]
    metrics: List[DomainResource]
    functions: List[DomainResource]
    total_tables: int = 0
    total_metrics: int = 0
    total_functions: int = 0
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "business_unit": self.business_unit,
            "tables": [t.__dict__ for t in self.tables],
            "metrics": [m.__dict__ for m in self.metrics],
            "functions": [f.__dict__ for f in self.functions],
            "total_tables": self.total_tables,
            "total_metrics": self.total_metrics,
            "total_functions": self.total_functions,
            "discovered_at": self.discovered_at,
        }


class DatabricksDiscoveryEngine:
    """
    Discovery engine for Databricks Unity Catalog.
    Reads table tags, comments, and metadata to find domain resources.
    """

    def __init__(self, connector: DatabricksConnector):
        self.connector = connector
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)

    def discover_domain(
        self,
        domain: str,
        business_unit: Optional[str] = None,
        catalog: str = "main"
    ) -> DomainProfile:
        """
        Discover all resources for a domain.

        Args:
            domain: Domain name (e.g., 'finance', 'marketing', 'sales')
            business_unit: Optional business unit filter
            catalog: Unity Catalog name

        Returns:
            DomainProfile with all discovered resources
        """
        cache_key = f"{domain}_{business_unit}_{catalog}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                logger.info(f"Using cached discovery for {domain}")
                return cached_data

        logger.info(f"Discovering domain: {domain}, business_unit: {business_unit}")

        with perf_logger.track("domain_discovery", {"domain": domain}):
            # Discover tables
            tables = self._discover_tables(domain, business_unit, catalog)

            # Discover metrics
            metrics = self._discover_metrics(domain, business_unit, catalog)

            # Discover functions
            functions = self._discover_functions(domain, business_unit, catalog)

            profile = DomainProfile(
                domain=domain,
                business_unit=business_unit,
                tables=tables,
                metrics=metrics,
                functions=functions,
                total_tables=len(tables),
                total_metrics=len(metrics),
                total_functions=len(functions),
            )

            # Cache results
            self.cache[cache_key] = (profile, datetime.now())

            logger.info(
                f"Discovered {len(tables)} tables, {len(metrics)} metrics, "
                f"{len(functions)} functions for domain {domain}"
            )

            return profile

    def _discover_tables(
        self, domain: str, business_unit: Optional[str], catalog: str
    ) -> List[DomainResource]:
        """Discover tables tagged with domain"""
        query = f"""
        SELECT
            table_catalog,
            table_schema,
            table_name,
            table_type,
            comment
        FROM {catalog}.information_schema.tables
        WHERE table_catalog = '{catalog}'
        """

        try:
            result = self.connector.execute_query(query)
            tables = []

            for row in result.rows:
                # Get table tags
                tags = self._get_table_tags(
                    catalog, row.get("table_schema"), row.get("table_name")
                )

                # Filter by domain tag
                if tags.get("domain") != domain:
                    continue

                # Filter by business unit if specified
                if business_unit and tags.get("business_unit") != business_unit:
                    continue

                # Get columns
                columns = self._get_table_columns(
                    catalog, row.get("table_schema"), row.get("table_name")
                )

                resource = DomainResource(
                    name=f"{row['table_schema']}.{row['table_name']}",
                    type=row.get("table_type", "TABLE").lower(),
                    domain=domain,
                    business_unit=tags.get("business_unit"),
                    description=row.get("comment"),
                    schema=row.get("table_schema"),
                    catalog=catalog,
                    tags=tags,
                    columns=columns,
                    owner=tags.get("owner"),
                )

                # Generate sample queries
                resource.sample_queries = self._generate_sample_queries(resource)

                tables.append(resource)

            return tables

        except Exception as e:
            logger.error(f"Error discovering tables: {e}", exc_info=True)
            return []

    def _get_table_tags(self, catalog: str, schema: str, table: str) -> Dict[str, str]:
        """
        Get tags for a table from Unity Catalog.

        Note: In real implementation, use:
        - Databricks SDK: workspace.tables.get(f"{catalog}.{schema}.{table}").tags
        - SQL: DESCRIBE TABLE EXTENDED and parse tags from properties
        """
        # Placeholder - in production, query actual Unity Catalog tags
        query = f"""
        DESCRIBE TABLE EXTENDED {catalog}.{schema}.{table}
        """

        try:
            result = self.connector.execute_query(query)
            tags = {}

            # Parse tags from DESCRIBE output
            for row in result.rows:
                col_name = row.get("col_name", "").lower()
                if col_name == "tags" or col_name == "tag":
                    data_type = row.get("data_type", "")
                    # Parse tags (format: {"domain":"finance","business_unit":"finance_bu"})
                    try:
                        tags = json.loads(data_type)
                    except:
                        pass

            return tags

        except Exception as e:
            logger.debug(f"Could not get tags for {table}: {e}")
            # For demo, return mock tags based on table name
            return self._infer_tags_from_name(table)

    def _infer_tags_from_name(self, table: str) -> Dict[str, str]:
        """Infer domain from table name (fallback)"""
        table_lower = table.lower()

        domain_keywords = {
            "finance": ["finance", "financial", "revenue", "cost", "budget", "invoice"],
            "marketing": ["marketing", "campaign", "lead", "customer", "conversion"],
            "sales": ["sales", "order", "transaction", "customer", "product"],
            "hr": ["employee", "payroll", "benefit", "hiring", "performance"],
            "operations": ["inventory", "supply", "logistics", "warehouse"],
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in table_lower for kw in keywords):
                return {"domain": domain}

        return {}

    def _get_table_columns(
        self, catalog: str, schema: str, table: str
    ) -> List[Dict[str, Any]]:
        """Get column information for a table"""
        query = f"""
        SELECT
            column_name,
            data_type,
            comment
        FROM {catalog}.information_schema.columns
        WHERE table_catalog = '{catalog}'
          AND table_schema = '{schema}'
          AND table_name = '{table}'
        ORDER BY ordinal_position
        """

        try:
            result = self.connector.execute_query(query)
            return [
                {
                    "name": row.get("column_name"),
                    "type": row.get("data_type"),
                    "description": row.get("comment"),
                }
                for row in result.rows
            ]
        except Exception as e:
            logger.debug(f"Could not get columns for {table}: {e}")
            return []

    def _discover_metrics(
        self, domain: str, business_unit: Optional[str], catalog: str
    ) -> List[DomainResource]:
        """Discover metric definitions (views with 'metric' in name/tags)"""
        # In Databricks, metrics might be:
        # 1. SQL queries stored in metadata
        # 2. Views with specific naming convention
        # 3. Lakehouse Monitoring metrics
        # 4. Entries in a metrics registry table

        query = f"""
        SELECT
            table_schema,
            table_name,
            comment
        FROM {catalog}.information_schema.views
        WHERE table_catalog = '{catalog}'
          AND (
              LOWER(table_name) LIKE '%metric%'
              OR LOWER(table_name) LIKE '%kpi%'
              OR LOWER(comment) LIKE '%metric%'
          )
        """

        try:
            result = self.connector.execute_query(query)
            metrics = []

            for row in result.rows:
                tags = self._get_table_tags(
                    catalog, row.get("table_schema"), row.get("table_name")
                )

                if tags.get("domain") != domain:
                    continue

                if business_unit and tags.get("business_unit") != business_unit:
                    continue

                resource = DomainResource(
                    name=f"{row['table_schema']}.{row['table_name']}",
                    type="metric",
                    domain=domain,
                    business_unit=tags.get("business_unit"),
                    description=row.get("comment"),
                    schema=row.get("table_schema"),
                    catalog=catalog,
                    tags=tags,
                )

                metrics.append(resource)

            return metrics

        except Exception as e:
            logger.error(f"Error discovering metrics: {e}", exc_info=True)
            return []

    def _discover_functions(
        self, domain: str, business_unit: Optional[str], catalog: str
    ) -> List[DomainResource]:
        """Discover Unity Catalog functions tagged with domain"""
        query = f"""
        SELECT
            function_schema,
            function_name,
            comment,
            routine_type
        FROM {catalog}.information_schema.routines
        WHERE routine_catalog = '{catalog}'
        """

        try:
            result = self.connector.execute_query(query)
            functions = []

            for row in result.rows:
                # Get function tags (similar to table tags)
                tags = self._infer_tags_from_name(row.get("function_name"))

                if tags.get("domain") != domain:
                    continue

                resource = DomainResource(
                    name=f"{row['function_schema']}.{row['function_name']}",
                    type="function",
                    domain=domain,
                    business_unit=tags.get("business_unit"),
                    description=row.get("comment"),
                    schema=row.get("function_schema"),
                    catalog=catalog,
                    tags=tags,
                )

                functions.append(resource)

            return functions

        except Exception as e:
            logger.error(f"Error discovering functions: {e}", exc_info=True)
            return []

    def _generate_sample_queries(self, resource: DomainResource) -> List[str]:
        """Generate sample SQL queries for a table"""
        full_name = f"{resource.catalog}.{resource.name}"

        queries = [
            f"-- View recent data\nSELECT * FROM {full_name} LIMIT 10",
            f"-- Count rows\nSELECT COUNT(*) as row_count FROM {full_name}",
        ]

        # Add domain-specific queries
        if resource.domain == "finance":
            if "revenue" in resource.name.lower():
                queries.append(
                    f"-- Total revenue\nSELECT SUM(revenue) as total_revenue FROM {full_name}"
                )
            if "invoice" in resource.name.lower():
                queries.append(
                    f"-- Pending invoices\nSELECT * FROM {full_name} WHERE status = 'PENDING'"
                )

        return queries


class SnowflakeDiscoveryEngine:
    """
    Discovery engine for Snowflake.
    Reads table tags, comments, and metadata to find domain resources.
    """

    def __init__(self, connector: SnowflakeConnector):
        self.connector = connector
        self.cache = {}
        self.cache_ttl = timedelta(hours=1)

    def discover_domain(
        self,
        domain: str,
        business_unit: Optional[str] = None,
        database: str = "CORTEX_AI"
    ) -> DomainProfile:
        """Discover all resources for a domain in Snowflake"""
        cache_key = f"{domain}_{business_unit}_{database}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                return cached_data

        logger.info(f"Discovering domain in Snowflake: {domain}")

        with perf_logger.track("domain_discovery_snowflake", {"domain": domain}):
            tables = self._discover_tables(domain, business_unit, database)
            metrics = self._discover_metrics(domain, business_unit, database)
            functions = self._discover_functions(domain, business_unit, database)

            profile = DomainProfile(
                domain=domain,
                business_unit=business_unit,
                tables=tables,
                metrics=metrics,
                functions=functions,
                total_tables=len(tables),
                total_metrics=len(metrics),
                total_functions=len(functions),
            )

            self.cache[cache_key] = (profile, datetime.now())
            return profile

    def _discover_tables(
        self, domain: str, business_unit: Optional[str], database: str
    ) -> List[DomainResource]:
        """Discover Snowflake tables with domain tags"""
        # Query Snowflake tag references
        query = f"""
        SELECT
            t.table_catalog,
            t.table_schema,
            t.table_name,
            t.table_type,
            t.comment,
            tag_ref.tag_value as domain_tag
        FROM {database}.INFORMATION_SCHEMA.TABLES t
        LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES tag_ref
            ON tag_ref.object_name = t.table_name
            AND tag_ref.tag_name = 'DOMAIN'
        WHERE t.table_catalog = '{database}'
          AND (tag_ref.tag_value = '{domain}' OR t.comment LIKE '%{domain}%')
        """

        try:
            result = self.connector.execute_query(query)
            tables = []

            for row in result.rows:
                columns = self._get_table_columns(
                    database, row.get("table_schema"), row.get("table_name")
                )

                resource = DomainResource(
                    name=f"{row['table_schema']}.{row['table_name']}",
                    type=row.get("table_type", "TABLE").lower(),
                    domain=domain,
                    description=row.get("comment"),
                    schema=row.get("table_schema"),
                    catalog=database,
                    columns=columns,
                )

                resource.sample_queries = self._generate_sample_queries(resource)
                tables.append(resource)

            return tables

        except Exception as e:
            logger.error(f"Error discovering Snowflake tables: {e}", exc_info=True)
            return []

    def _get_table_columns(
        self, database: str, schema: str, table: str
    ) -> List[Dict[str, Any]]:
        """Get column information"""
        query = f"""
        SELECT column_name, data_type, comment
        FROM {database}.INFORMATION_SCHEMA.COLUMNS
        WHERE table_schema = '{schema}'
          AND table_name = '{table}'
        ORDER BY ordinal_position
        """

        try:
            result = self.connector.execute_query(query)
            return [
                {
                    "name": row.get("column_name"),
                    "type": row.get("data_type"),
                    "description": row.get("comment"),
                }
                for row in result.rows
            ]
        except:
            return []

    def _discover_metrics(
        self, domain: str, business_unit: Optional[str], database: str
    ) -> List[DomainResource]:
        """Discover Snowflake metrics from semantic layer"""
        # Query metrics from Snowflake semantic layer or metric views
        return []

    def _discover_functions(
        self, domain: str, business_unit: Optional[str], database: str
    ) -> List[DomainResource]:
        """Discover Snowflake UDFs with domain tags"""
        return []

    def _generate_sample_queries(self, resource: DomainResource) -> List[str]:
        """Generate sample queries for Snowflake"""
        full_name = f"{resource.catalog}.{resource.name}"
        return [
            f"SELECT * FROM {full_name} LIMIT 10;",
            f"SELECT COUNT(*) FROM {full_name};",
        ]


class DomainDiscoveryEngine:
    """
    Main discovery engine that works with both Databricks and Snowflake.
    """

    def __init__(self, platform_config: PlatformConfig):
        self.platform_config = platform_config

        if platform_config.is_databricks():
            connector = DatabricksConnector()
            self.engine = DatabricksDiscoveryEngine(connector)
        elif platform_config.is_snowflake():
            connector = SnowflakeConnector()
            self.engine = SnowflakeDiscoveryEngine(connector)
        else:
            # Local mode - return mock data
            self.engine = None

    def discover_domain(
        self, domain: str, business_unit: Optional[str] = None
    ) -> DomainProfile:
        """Discover all resources for a domain"""
        if self.engine is None:
            # Return mock data for local development
            return self._get_mock_profile(domain, business_unit)

        return self.engine.discover_domain(domain, business_unit)

    def list_available_domains(self) -> List[Dict[str, Any]]:
        """List all available domains in the catalog"""
        # Query all unique domain tags
        if self.platform_config.is_databricks():
            # Query Unity Catalog for unique domain tags
            return [
                {"name": "finance", "description": "Financial data and metrics"},
                {"name": "marketing", "description": "Marketing campaigns and analytics"},
                {"name": "sales", "description": "Sales transactions and forecasting"},
                {"name": "hr", "description": "Human resources and payroll"},
            ]
        elif self.platform_config.is_snowflake():
            # Query Snowflake tag values
            return [
                {"name": "finance", "description": "Financial data and metrics"},
                {"name": "marketing", "description": "Marketing campaigns and analytics"},
            ]
        else:
            return [
                {"name": "finance", "description": "Financial data and metrics"},
                {"name": "marketing", "description": "Marketing campaigns and analytics"},
                {"name": "sales", "description": "Sales transactions and forecasting"},
            ]

    def create_domain_agent_config(
        self, domain: str, business_unit: Optional[str] = None, role: str = "analyst"
    ) -> Dict[str, Any]:
        """
        Auto-generate agent configuration based on discovered domain resources.

        Returns agent config dict that can be used with AgentBuilder.
        """
        profile = self.discover_domain(domain, business_unit)

        # Generate agent name and description
        bu_prefix = f"{business_unit.upper()} " if business_unit else ""
        agent_name = f"{bu_prefix}{domain.title()} {role.title()}"

        # Build system prompt with discovered resources
        system_prompt = self._build_domain_prompt(profile, role)

        # Build tools list (platform-specific functions)
        tools = [f.name for f in profile.functions[:10]]  # Limit to 10 functions

        # Add standard tools
        tools.extend(["sql_executor", "data_visualizer"])

        return {
            "name": agent_name,
            "description": f"Specialized {role} for {domain} domain",
            "system_prompt": system_prompt,
            "model_provider": "openai",
            "model_name": "gpt-4",
            "temperature": 0.2,
            "tools": tools,
            "enable_memory": True,
            "metadata": {
                "domain": domain,
                "business_unit": business_unit,
                "discovered_tables": len(profile.tables),
                "discovered_metrics": len(profile.metrics),
                "auto_generated": True,
            },
        }

    def _build_domain_prompt(self, profile: DomainProfile, role: str) -> str:
        """Build system prompt with discovered resources"""
        prompt_parts = [
            f"You are a specialized {role} working in the {profile.domain} domain.",
        ]

        if profile.business_unit:
            prompt_parts.append(f"You work in the {profile.business_unit} business unit.")

        prompt_parts.append("\n## Available Data Sources\n")
        prompt_parts.append(
            f"You have access to {profile.total_tables} tables, {profile.total_metrics} metrics, "
            f"and {profile.total_functions} specialized functions.\n"
        )

        # Add table information
        if profile.tables:
            prompt_parts.append("### Key Tables:")
            for table in profile.tables[:10]:  # Top 10 tables
                desc = table.description or "No description"
                prompt_parts.append(f"- **{table.name}**: {desc}")
                if table.columns:
                    cols = ", ".join([c["name"] for c in table.columns[:5]])
                    prompt_parts.append(f"  Columns: {cols}")

        # Add metrics
        if profile.metrics:
            prompt_parts.append("\n### Available Metrics:")
            for metric in profile.metrics[:5]:
                desc = metric.description or "No description"
                prompt_parts.append(f"- **{metric.name}**: {desc}")

        # Add guidance
        prompt_parts.append("\n## Guidance:")
        prompt_parts.append(
            "- Use SQL queries to analyze data from the tables listed above"
        )
        prompt_parts.append("- Reference metrics for standard calculations")
        prompt_parts.append("- Provide business context in your analysis")
        prompt_parts.append("- Generate visualizations when helpful")

        return "\n".join(prompt_parts)

    def _get_mock_profile(self, domain: str, business_unit: Optional[str]) -> DomainProfile:
        """Return mock data for local development"""
        mock_tables = [
            DomainResource(
                name=f"{domain}_revenue",
                type="table",
                domain=domain,
                business_unit=business_unit,
                description=f"Revenue data for {domain}",
                columns=[
                    {"name": "date", "type": "DATE"},
                    {"name": "revenue", "type": "DECIMAL(18,2)"},
                    {"name": "region", "type": "VARCHAR"},
                ],
                sample_queries=[f"SELECT * FROM {domain}_revenue LIMIT 10"],
            ),
            DomainResource(
                name=f"{domain}_transactions",
                type="table",
                domain=domain,
                description=f"Transaction details for {domain}",
                columns=[
                    {"name": "transaction_id", "type": "VARCHAR"},
                    {"name": "amount", "type": "DECIMAL(18,2)"},
                    {"name": "customer_id", "type": "VARCHAR"},
                ],
            ),
        ]

        mock_metrics = [
            DomainResource(
                name=f"total_{domain}_revenue",
                type="metric",
                domain=domain,
                description=f"Total revenue for {domain} domain",
            )
        ]

        return DomainProfile(
            domain=domain,
            business_unit=business_unit,
            tables=mock_tables,
            metrics=mock_metrics,
            functions=[],
            total_tables=len(mock_tables),
            total_metrics=len(mock_metrics),
            total_functions=0,
        )


# Convenience function
def discover_and_create_agent(
    platform_config: PlatformConfig,
    domain: str,
    business_unit: Optional[str] = None,
    role: str = "analyst",
) -> Dict[str, Any]:
    """
    One-step function to discover domain and create agent config.

    Usage:
        config = discover_and_create_agent(
            platform_config,
            domain="finance",
            business_unit="finance_bu",
            role="analyst"
        )
    """
    engine = DomainDiscoveryEngine(platform_config)
    return engine.create_domain_agent_config(domain, business_unit, role)
