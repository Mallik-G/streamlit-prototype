# Development Guide

## Table of Contents
1. [Setup](#setup)
2. [Logging & Debugging](#logging--debugging)
3. [Testing](#testing)
4. [CI/CD](#cicd)
5. [Docker Development](#docker-development)
6. [Code Quality](#code-quality)

---

## Setup

### Local Development

```bash
# Clone repository
git clone <repo-url>
cd streamlit-prototype

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov pytest-mock ruff black isort mypy pre-commit

# Install pre-commit hooks
pre-commit install

# Run application
streamlit run app.py
```

### Environment Variables

Create `.env` file:
```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Platform
DEPLOYMENT_PLATFORM=local  # or snowflake, databricks

# Logging
DEBUG=true
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
STRUCTURED_LOGGING=false  # Use JSON logs in production

# Snowflake (if applicable)
SNOWFLAKE_ACCOUNT=...
SNOWFLAKE_USER=...
SNOWFLAKE_PASSWORD=...
SNOWFLAKE_WAREHOUSE=...
SNOWFLAKE_DATABASE=...

# Databricks (if applicable)
DATABRICKS_HOST=https://...
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/...
DATABRICKS_TOKEN=dapi...
DATABRICKS_CATALOG=main
```

---

## Logging & Debugging

### Logging Levels

```python
from utils.logging_config import get_logger

logger = get_logger("my_module")

logger.debug("Detailed information for diagnosing problems")
logger.info("General informational messages")
logger.warning("Warning messages for potentially harmful situations")
logger.error("Error messages", exc_info=True)
logger.critical("Critical issues that may cause app failure")
```

### Structured Logging

For production, use structured JSON logging:

```bash
STRUCTURED_LOGGING=true streamlit run app.py
```

Output:
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "logger": "workflow_builder",
  "message": "Workflow executed successfully",
  "module": "workflow_builder",
  "function": "execute",
  "line": 345,
  "workflow_id": "abc-123",
  "duration_seconds": 12.5
}
```

### Performance Tracking

Track operation performance:

```python
from utils.logging_config import get_performance_logger

perf = get_performance_logger()

# Track execution time
with perf.track("workflow_execution", {"workflow_id": workflow.id}):
    result = executor.execute()

# Get metrics
metrics = perf.get_metrics()
# {
#   "workflow_execution": {
#     "count": 10,
#     "avg_duration": 12.3,
#     "min_duration": 8.1,
#     "max_duration": 18.7,
#     "failure_rate": 0.1
#   }
# }
```

### Audit Logging

Track user actions for compliance:

```python
from utils.logging_config import get_audit_logger

audit = get_audit_logger()

audit.log_action(
    action="create",
    resource_type="workflow",
    resource_id=workflow.id,
    user_id="user@example.com",
    metadata={"workflow_name": workflow.name},
    status="success"
)
```

### Debug Mode

Enable detailed debugging:

```bash
DEBUG=true streamlit run app.py
```

```python
from utils.logging_config import get_debug_context

debug = get_debug_context()

if debug.enabled:
    debug.trace("agent_execution", "Starting agent", {"agent_id": agent.id})
    debug.trace("agent_execution", "Prompt sent", {"prompt": prompt})
    debug.trace("agent_execution", "Response received", {"response": response})

# Get all traces
traces = debug.get_traces()
```

### Platform-Specific Logging

#### Snowflake
Logs are automatically shipped to `CORTEX_AI_LOGS` table:

```sql
CREATE TABLE CORTEX_AI_LOGS (
    timestamp TIMESTAMP_NTZ,
    level VARCHAR,
    logger VARCHAR,
    message VARCHAR,
    module VARCHAR,
    function VARCHAR
);

-- Query logs
SELECT * FROM CORTEX_AI_LOGS
WHERE level = 'ERROR'
  AND timestamp > DATEADD(hour, -1, CURRENT_TIMESTAMP())
ORDER BY timestamp DESC;
```

#### Databricks
Logs are shipped to Delta table `cortex_ai_logs`:

```python
# Query logs with PySpark
logs_df = spark.table("cortex_ai_logs")

# Filter errors in last hour
errors = logs_df.filter(
    (F.col("level") == "ERROR") &
    (F.col("timestamp") > F.current_timestamp() - F.expr("INTERVAL 1 HOUR"))
)
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific markers
pytest tests/ -m unit          # Unit tests only
pytest tests/ -m integration   # Integration tests only
pytest tests/ -m "not slow"    # Skip slow tests

# Run specific test file
pytest tests/test_workflow_builder.py

# Run specific test
pytest tests/test_workflow_builder.py::TestWorkflowConfig::test_create_workflow_config

# Verbose output
pytest tests/ -v

# Stop on first failure
pytest tests/ -x
```

### Writing Tests

```python
import pytest

@pytest.mark.unit
def test_simple_function():
    """Test a simple function"""
    result = my_function(42)
    assert result == 84

@pytest.mark.integration
def test_workflow_execution():
    """Test workflow execution"""
    # This test requires external dependencies
    workflow = create_test_workflow()
    result = execute_workflow(workflow)
    assert result["success"] == True

@pytest.mark.slow
def test_large_dataset():
    """Test with large dataset (slow)"""
    # This test takes a long time
    pass

# Fixtures
@pytest.fixture
def sample_workflow():
    """Fixture that provides a sample workflow"""
    return WorkflowConfig(...)

def test_with_fixture(sample_workflow):
    """Test using a fixture"""
    assert sample_workflow.name == "Test"
```

### Test Coverage

View coverage report:
```bash
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

---

## CI/CD

### GitHub Actions

Workflows are defined in `.github/workflows/ci.yml`:

- **Lint**: Runs ruff, black, isort, mypy
- **Security**: Runs bandit security scanner
- **Test**: Runs pytest with coverage
- **Build**: Builds Docker image
- **Deploy**: Deploys to staging/production

### Running CI Locally

```bash
# Linting
ruff check .
black --check .
isort --check-only .
mypy .

# Security scan
bandit -r . -f json -o bandit-report.json

# Tests
pytest tests/ --cov=. --cov-report=xml

# Build Docker image
docker build -t cortex-ai:local .
```

### Pre-commit Hooks

Automatically run checks before commits:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

### Deployment

#### To Streamlit Cloud

```bash
# Push to main branch triggers automatic deployment
git push origin main
```

#### To Snowflake

```bash
# Build and deploy
docker build -t cortex-ai:production .
# Push to Snowflake registry
# Deploy via Snowpark Container Services
```

#### To Databricks

```bash
# Deploy as Databricks App
databricks apps deploy cortex-ai \
  --source-code-path . \
  --config deployment/databricks-app.yml
```

---

## Docker Development

### Using Docker Compose

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild containers
docker-compose up --build

# Start with optional services
docker-compose --profile with-db up  # Include PostgreSQL
docker-compose --profile with-cache up  # Include Redis
```

### Docker Commands

```bash
# Build production image
docker build -t cortex-ai:prod --target production .

# Build development image
docker build -t cortex-ai:dev --target development .

# Run container
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/agents:/app/agents \
  cortex-ai:prod

# Shell into running container
docker exec -it <container-id> /bin/bash

# View logs
docker logs -f <container-id>
```

### Multi-stage Builds

Our Dockerfile uses multi-stage builds for efficiency:

- **base**: Common dependencies
- **development**: Includes dev tools (pytest, ruff, etc.)
- **production**: Minimal image, no dev dependencies

---

## Code Quality

### Code Formatting

```bash
# Format code with black
black .

# Sort imports with isort
isort .

# Auto-fix linting issues
ruff check . --fix
```

### Type Checking

```bash
# Run mypy
mypy . --ignore-missing-imports

# Check specific file
mypy workflow_builder.py
```

### Code Style Guidelines

- **Line length**: 100 characters
- **Docstrings**: Google style
- **Imports**: Sorted by isort (stdlib, third-party, local)
- **Type hints**: Use where helpful, not required everywhere
- **Naming**:
  - `snake_case` for functions and variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants

Example:
```python
"""
Module docstring explaining purpose.
"""
from typing import Dict, List, Optional

from external_library import something

from utils.logging_config import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 3  # Constant


class MyClass:
    """Class docstring.

    Args:
        name: Description of name parameter
        config: Optional configuration dict
    """

    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or {}

    def process(self, data: List[str]) -> Dict[str, any]:
        """Process data and return results.

        Args:
            data: List of strings to process

        Returns:
            Dictionary containing processed results

        Raises:
            ValueError: If data is empty
        """
        if not data:
            raise ValueError("Data cannot be empty")

        logger.info(f"Processing {len(data)} items")
        return {"count": len(data)}
```

---

## Debugging Common Issues

### Issue: Streamlit not starting

```bash
# Check if port is in use
lsof -i :8501

# Try different port
streamlit run app.py --server.port=8502

# Clear cache
streamlit cache clear
```

### Issue: Import errors

```bash
# Ensure you're in the right directory
pwd  # Should be streamlit-prototype/

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: Tests failing

```bash
# Run with verbose output
pytest tests/ -vv

# Run with print statements
pytest tests/ -s

# Debug specific test
pytest tests/test_workflow_builder.py::test_name --pdb
```

### Issue: Docker container won't start

```bash
# Check logs
docker-compose logs app

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up
```

---

## Performance Profiling

### Using cProfile

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = execute_workflow(workflow)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(20)  # Top 20 functions
```

### Using line_profiler

```bash
# Install
pip install line_profiler

# Add @profile decorator to function
@profile
def my_function():
    ...

# Run
kernprof -l -v script.py
```

---

## Resources

- [Streamlit Docs](https://docs.streamlit.io)
- [LangChain Docs](https://python.langchain.com)
- [Pytest Docs](https://docs.pytest.org)
- [Docker Docs](https://docs.docker.com)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

---

## Getting Help

- Check documentation in `/docs` folder
- Review example files in `examples/`
- Open an issue on GitHub
- Ask in team chat
