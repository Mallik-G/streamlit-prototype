# RAG & Vector Search Guide

Complete guide for building knowledge-based agents with Retrieval-Augmented Generation (RAG) capabilities.

## Overview

The Knowledge Base system enables agents to access and reason over your custom documents through vector search. Agents can retrieve relevant context from uploaded documents to provide more accurate, grounded responses.

## Platform Support

### ❄️ Snowflake
- **Storage**: Snowflake Stages (`@MY_STAGE`)
- **Vector Search**: Cortex Search services
- **Embeddings**: Cortex embedding models (snowflake-arctic-embed, e5-base-v2)
- **SQL Integration**: Native SQL queries with Cortex functions

### 🧱 Databricks
- **Storage**: Unity Catalog Volumes (`/Volumes/catalog/schema/volume`)
- **Vector Search**: Databricks Vector Search with endpoints
- **Embeddings**: databricks-bge-large-en, databricks-gte-large-en
- **Integration**: Delta tables, MLflow tracking

### 💻 Local
- **Storage**: Local filesystem
- **Vector Search**: ChromaDB
- **Embeddings**: OpenAI text-embedding models
- **Use Case**: Development, testing, small-scale deployments

## Getting Started

### 1. Upload Documents

Navigate to **📚 Knowledge Base** → **Upload Documents**

#### Step 1: Choose Platform
Select your platform (Local, Snowflake, or Databricks)

#### Step 2: Configure Storage

**Snowflake:**
```sql
-- Create stage for documents
CREATE STAGE MY_DOCS_STAGE;

-- Upload files
PUT file://path/to/doc.pdf @MY_DOCS_STAGE;
```

**Databricks:**
```python
# Create Unity Catalog volume
%sql CREATE VOLUME main.default.my_docs;

# Upload via CLI
databricks fs cp doc.pdf dbfs:/Volumes/main/default/my_docs/
```

**Local:**
- Files stored in `./documents` directory
- Automatically managed

#### Step 3: Upload Files
- Supported formats: TXT, MD, PDF, DOCX, CSV
- Multiple files at once
- Automatic chunking and embedding

#### Step 4: Configure Chunking
```
Chunk Size: 1000 characters
Chunk Overlap: 200 characters
```

Adjust based on your content:
- **Technical docs**: 500-800 chars, low overlap
- **General text**: 1000-1500 chars, medium overlap
- **Code**: 300-500 chars, high overlap

### 2. Create Vector Search Index

**Option A: During Upload**
- Select "Create New Index"
- Name your index
- Documents automatically ingested

**Option B: Manual Creation**

**Snowflake:**
```sql
CREATE CORTEX SEARCH SERVICE my_knowledge_base
ON text_column
WAREHOUSE = COMPUTE_WH
TARGET_LAG = '1 minute'
AS (
    SELECT id, text, metadata
    FROM my_documents_table
);
```

**Databricks:**
```python
from databricks.vector_search.client import VectorSearchClient

client = VectorSearchClient()
client.create_delta_sync_index(
    endpoint_name="my_endpoint",
    index_name="main.default.kb_index",
    source_table_name="main.default.documents",
    pipeline_type="TRIGGERED",
    primary_key="id",
    embedding_dimension=1536,
    embedding_vector_column="embedding"
)
```

### 3. Create RAG-Enabled Agent

Navigate to **🔧 Agent Builder** → **Create New Agent**

#### Configure Agent

1. **Basic Info**: Name, description, category
2. **Model**: Choose LLM and temperature
3. **System Prompt**: Include RAG instructions
4. **Advanced Settings**:
   - ✅ Enable RAG
   - Select knowledge base index
   - RAG tool automatically added

#### Example System Prompt for RAG

```
You are a knowledgeable assistant with access to our company documentation.

When answering questions:
1. Search the knowledge base for relevant context
2. Use the retrieved information to provide accurate answers
3. Cite sources when using specific information
4. If information isn't in the knowledge base, say so clearly
5. Don't make up information - stick to the facts

Format citations as [Source: filename.pdf]
```

### 4. Test Your Agent

1. Load the agent in chat
2. Ask questions about your documents
3. Agent will automatically:
   - Retrieve relevant context
   - Generate informed responses
   - Include source citations

## Architecture

### Document Flow

```
1. Upload → 2. Chunk → 3. Embed → 4. Store → 5. Search → 6. Retrieve
```

#### 1. Upload
Documents uploaded via UI or API

#### 2. Chunk
Text split into manageable pieces:
- Configurable chunk size
- Overlap for context continuity
- Sentence boundary detection

#### 3. Embed
Convert chunks to vectors:
- **Snowflake**: `SNOWFLAKE.CORTEX.EMBED_TEXT_768()`
- **Databricks**: Model endpoint or external API
- **Local**: OpenAI embeddings API

#### 4. Store
Vectors saved to index:
- **Snowflake**: Cortex Search service
- **Databricks**: Vector Search index + Delta table
- **Local**: ChromaDB collection

#### 5. Search
Query converted to vector, similarity search performed

#### 6. Retrieve
Top-k most similar chunks returned with metadata

### RAG Execution Flow

```
User Query
    ↓
[Query Embedding]
    ↓
[Vector Search] → Top K Results
    ↓
[Context Assembly]
    ↓
[LLM Prompt] ← Original Query + Retrieved Context
    ↓
[Generated Response]
```

## API Reference

### VectorSearchConfig

```python
from utils.vector_search import VectorSearchConfig

config = VectorSearchConfig(
    id="unique_id",
    name="My Knowledge Base",
    provider="snowflake",  # or "databricks", "local"
    index_name="kb_index",
    embedding_model="snowflake-arctic-embed-m",
    volume_path="MY_DB.PUBLIC.@MY_STAGE",
    endpoint_name="MY_DB.PUBLIC.CORTEX_SEARCH_KB",
    dimension=768,
    distance_metric="cosine",
    top_k=5
)
```

### Document Ingestion

```python
from utils.vector_search import DocumentIngestion

ingestion = DocumentIngestion(
    chunk_size=1000,
    chunk_overlap=200
)

# Process a file
documents = ingestion.process_file("document.pdf")

# Each document has:
# {
#     "id": "doc_chunk_0",
#     "text": "chunk content...",
#     "metadata": {
#         "source": "document.pdf",
#         "page": 1,
#         "chunk_index": 0
#     }
# }
```

### Vector Search

```python
from utils.vector_search import get_vector_search

# Get search instance
vector_search = get_vector_search(config)
vector_search.connect()

# Search
results = vector_search.search(
    query="What is the refund policy?",
    top_k=5
)

# Results format:
# [
#     {
#         "id": "doc_chunk_42",
#         "text": "Our refund policy...",
#         "metadata": {"source": "policy.pdf"},
#         "distance": 0.23
#     },
#     ...
# ]
```

### RAG Tool for Agents

```python
from utils.vector_search import RAGTool

# Initialize RAG tool with vector config
rag_tool = RAGTool(vector_config)

# Retrieve context
context = rag_tool.retrieve_context("user query", top_k=5)

# Or get full answer with LLM
answer = rag_tool.answer_with_context(
    query="What are the business hours?",
    llm_response_func=lambda prompt: llm.generate(prompt)
)
```

## Snowflake-Specific Features

### Cortex Search

```sql
-- Create search service
CREATE CORTEX SEARCH SERVICE product_docs_search
ON content
WAREHOUSE = COMPUTE_WH
TARGET_LAG = '1 minute'
AS (
    SELECT id, content, metadata
    FROM product_documentation
);

-- Search
SELECT * FROM TABLE(
    product_docs_search.SEARCH(
        query => 'installation instructions',
        num_results => 5
    )
);
```

### Cortex Embeddings

```sql
-- Generate embeddings
SELECT
    id,
    content,
    SNOWFLAKE.CORTEX.EMBED_TEXT_768(
        'snowflake-arctic-embed-m',
        content
    ) as embedding
FROM documents;

-- Similarity search
SELECT
    id,
    content,
    VECTOR_COSINE_SIMILARITY(
        embedding,
        SNOWFLAKE.CORTEX.EMBED_TEXT_768(
            'snowflake-arctic-embed-m',
            'search query'
        )
    ) as similarity
FROM documents_with_embeddings
ORDER BY similarity DESC
LIMIT 5;
```

### Stages for Documents

```sql
-- Create internal stage
CREATE STAGE company_docs;

-- Create external stage (S3)
CREATE STAGE external_docs
URL = 's3://my-bucket/docs/'
CREDENTIALS = (AWS_KEY_ID='...' AWS_SECRET_KEY='...');

-- Upload files
PUT file://local_doc.pdf @company_docs;

-- List files
LIST @company_docs;

-- Load into table
COPY INTO raw_documents
FROM @company_docs
FILE_FORMAT = (TYPE = 'CSV');
```

## Databricks-Specific Features

### Unity Catalog Volumes

```python
# Create volume
%sql CREATE VOLUME main.default.company_docs;

# Upload via Databricks CLI
!databricks fs cp doc.pdf dbfs:/Volumes/main/default/company_docs/

# List files
%fs ls /Volumes/main/default/company_docs/

# Read in Spark
df = spark.read.text("/Volumes/main/default/company_docs/")
```

### Vector Search

```python
from databricks.vector_search.client import VectorSearchClient

client = VectorSearchClient()

# Create endpoint
client.create_endpoint("my_vs_endpoint")

# Create index
index = client.create_delta_sync_index(
    endpoint_name="my_vs_endpoint",
    index_name="main.default.docs_index",
    source_table_name="main.default.documents",
    pipeline_type="TRIGGERED",
    primary_key="id",
    embedding_dimension=1536,
    embedding_vector_column="embedding"
)

# Search
results = index.similarity_search(
    query_text="installation guide",
    columns=["id", "content", "metadata"],
    num_results=5
)
```

### Delta Tables for Documents

```python
# Create documents table
%sql
CREATE TABLE main.default.documents (
    id STRING,
    content STRING,
    metadata MAP<STRING, STRING>,
    embedding ARRAY<FLOAT>
)
USING DELTA;

# Compute embeddings (using external model)
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(documents['content'].tolist())

# Add embeddings to DataFrame
df = df.withColumn("embedding", embeddings)
df.write.mode("append").saveAsTable("main.default.documents")
```

## Best Practices

### Document Preparation

1. **Clean Text**: Remove headers, footers, page numbers
2. **Consistent Format**: Standardize before upload
3. **Metadata**: Include useful metadata (date, author, category)
4. **Chunking**: Tune based on document type

### Embedding Strategy

1. **Model Selection**:
   - **General**: text-embedding-ada-002, snowflake-arctic-embed-m
   - **Code**: openai-code-search, databricks-bge-large-en
   - **Multilingual**: multilingual-e5-large

2. **Dimension Tradeoffs**:
   - **768**: Good balance of performance and cost
   - **1536**: Higher quality, more expensive
   - **384**: Faster, smaller storage, lower quality

### Search Optimization

1. **Top-K Selection**:
   - Start with 3-5 results
   - Increase for complex queries
   - Balance relevance vs context length

2. **Reranking**:
   - Use LLM to rerank results
   - Filter by metadata
   - Boost recent documents

3. **Hybrid Search**:
   - Combine vector + keyword search
   - Especially useful for exact matches

### Agent Configuration

1. **System Prompt**:
   - Explicitly mention RAG capability
   - Provide citation format
   - Set expectations

2. **Temperature**:
   - Lower (0.2-0.4) for factual answers
   - Medium (0.5-0.7) for balanced
   - Higher (0.8-1.0) for creative synthesis

3. **Context Window**:
   - Reserve tokens for retrieved context
   - Balance query + context + response
   - Consider max_tokens limit

## Troubleshooting

### No Results Returned

**Check:**
- Index exists and has documents
- Embedding model matches index
- Query is meaningful
- Connection to platform

**Fix:**
```python
# Verify index
indexes = vector_manager.list_configs()
print(f"Found {len(indexes)} indexes")

# Test connection
vector_search = get_vector_search(config)
connected = vector_search.connect()
print(f"Connected: {connected}")
```

### Poor Quality Results

**Check:**
- Chunk size too large/small
- Wrong embedding model
- Query too broad/specific
- Insufficient documents

**Fix:**
- Adjust chunk_size (try 800-1200)
- Increase chunk_overlap
- Use more specific queries
- Add more relevant documents

### Platform Errors

**Snowflake:**
```
Error: Cortex Search service not found
→ Verify service name and permissions
→ Check warehouse is running
```

**Databricks:**
```
Error: Vector Search endpoint not found
→ Create endpoint first
→ Check cluster has access
```

**Local:**
```
Error: ChromaDB collection not found
→ Reinitialize connection
→ Check persist_directory path
```

## Examples

### Customer Support Agent

```python
# System prompt
system_prompt = """
You are a customer support agent with access to our product documentation and FAQ.

When users ask questions:
1. Search the knowledge base for relevant answers
2. Provide clear, helpful responses based on the documentation
3. Include document references [Source: filename.pdf]
4. If the answer isn't in the docs, offer to escalate to human support

Be friendly, patient, and thorough.
"""

# Knowledge base
- product_manual.pdf
- faq.pdf
- troubleshooting_guide.pdf
- return_policy.pdf
```

### Code Documentation Assistant

```python
# System prompt
system_prompt = """
You are a code documentation assistant for our Python codebase.

When developers ask questions:
1. Search code docs and API references
2. Provide code examples from the documentation
3. Explain concepts clearly with references
4. Link to relevant sections [Source: module_name.py]

Include working code snippets when helpful.
"""

# Knowledge base
- api_reference.md
- architecture_guide.md
- example_code/*.py
- tutorials/*.md
```

### Research Assistant

```python
# System prompt
system_prompt = """
You are a research assistant with access to academic papers and reports.

When answering research questions:
1. Search the knowledge base for relevant studies
2. Synthesize information from multiple sources
3. Cite all sources properly [Paper: title, year]
4. Distinguish between facts, findings, and interpretations

Maintain academic rigor and objectivity.
"""

# Knowledge base
- research_papers/*.pdf
- reports/*.pdf
- datasets/*.csv
- literature_reviews/*.md
```

## Roadmap

Planned enhancements:

- [ ] Hybrid search (vector + keyword)
- [ ] Result reranking with LLM
- [ ] Automatic metadata extraction
- [ ] Multi-modal search (images, tables)
- [ ] Citation tracking and links
- [ ] Document versioning
- [ ] Real-time index updates
- [ ] Query analytics
- [ ] A/B testing for retrieval strategies
- [ ] Cost optimization tools

## Support

For issues or questions:
- Check platform documentation (Snowflake Cortex, Databricks Vector Search)
- Review example implementations
- Test with small datasets first
- Monitor embedding costs
