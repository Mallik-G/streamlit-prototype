"""
Vector Search Module - Document Ingestion and RAG
Supports Databricks Vector Search, Snowflake Cortex Search, and local embeddings
"""
import os
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class VectorSearchConfig:
    """Configuration for vector search"""
    id: str
    name: str
    provider: str  # 'databricks', 'snowflake', 'local', 'pinecone', 'weaviate'
    index_name: str
    embedding_model: str
    volume_path: Optional[str] = None  # For Databricks volumes
    endpoint_name: Optional[str] = None  # For Databricks
    dimension: int = 1536  # Embedding dimension
    distance_metric: str = "cosine"
    top_k: int = 5
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class VectorSearchManager:
    """Manage vector search indexes and document ingestion"""

    def __init__(self, config_path: str = "vector_configs"):
        self.config_path = config_path
        os.makedirs(config_path, exist_ok=True)

    def create_index(
        self,
        name: str,
        provider: str,
        embedding_model: str = "text-embedding-ada-002",
        **kwargs
    ) -> VectorSearchConfig:
        """Create a new vector search index"""
        import uuid

        config = VectorSearchConfig(
            id=str(uuid.uuid4()),
            name=name,
            provider=provider,
            index_name=name.lower().replace(" ", "_"),
            embedding_model=embedding_model,
            **kwargs
        )

        self._save_config(config)
        return config

    def _save_config(self, config: VectorSearchConfig):
        """Save vector search configuration"""
        file_path = os.path.join(self.config_path, f"{config.id}.json")
        with open(file_path, 'w') as f:
            json.dump(config.__dict__, f, indent=2)

    def load_config(self, config_id: str) -> Optional[VectorSearchConfig]:
        """Load vector search configuration"""
        file_path = os.path.join(self.config_path, f"{config_id}.json")
        if not os.path.exists(file_path):
            return None

        with open(file_path, 'r') as f:
            data = json.load(f)
            return VectorSearchConfig(**data)

    def list_configs(self) -> List[VectorSearchConfig]:
        """List all vector search configurations"""
        configs = []
        for filename in os.listdir(self.config_path):
            if filename.endswith('.json'):
                with open(os.path.join(self.config_path, filename), 'r') as f:
                    data = json.load(f)
                    configs.append(VectorSearchConfig(**data))
        return configs

    def delete_config(self, config_id: str) -> bool:
        """Delete vector search configuration"""
        file_path = os.path.join(self.config_path, f"{config_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False


class DatabricksVectorSearch:
    """Databricks Vector Search integration"""

    def __init__(self, config: VectorSearchConfig):
        self.config = config
        self.client = None
        self.index = None

    def connect(self):
        """Connect to Databricks Vector Search"""
        try:
            from databricks.vector_search.client import VectorSearchClient

            self.client = VectorSearchClient()
            self.index = self.client.get_index(
                endpoint_name=self.config.endpoint_name,
                index_name=self.config.index_name
            )
            return True
        except ImportError:
            print("Databricks Vector Search not installed. Install: pip install databricks-vectorsearch")
            return False
        except Exception as e:
            print(f"Databricks Vector Search connection error: {e}")
            return False

    def create_index(self, source_table: str):
        """Create a new vector search index"""
        if not self.client:
            return False

        try:
            self.index = self.client.create_delta_sync_index(
                endpoint_name=self.config.endpoint_name,
                index_name=self.config.index_name,
                source_table_name=source_table,
                pipeline_type="TRIGGERED",
                primary_key="id",
                embedding_dimension=self.config.dimension,
                embedding_vector_column="embedding"
            )
            return True
        except Exception as e:
            print(f"Error creating index: {e}")
            return False

    def search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search the vector index"""
        if not self.index:
            self.connect()

        k = top_k or self.config.top_k

        try:
            results = self.index.similarity_search(
                query_text=query,
                columns=["id", "text", "metadata"],
                num_results=k
            )
            return results.get("result", {}).get("data_array", [])
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def ingest_documents(self, documents: List[Dict[str, Any]]):
        """Ingest documents into the index"""
        # For Databricks, documents are typically ingested via Delta tables
        # This is a placeholder for the ingestion logic
        pass


class SnowflakeCortexSearch:
    """Snowflake Cortex Search integration"""

    def __init__(self, config: VectorSearchConfig):
        self.config = config
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

            self.session = Session.builder.configs(connection_parameters).create()
            return True
        except Exception as e:
            print(f"Snowflake connection error: {e}")
            return False

    def create_index(self, table_name: str, text_column: str):
        """Create Cortex Search index"""
        if not self.session:
            self.connect()

        try:
            # Create Cortex Search service
            sql = f"""
            CREATE CORTEX SEARCH SERVICE {self.config.index_name}
            ON {text_column}
            WAREHOUSE = {os.getenv('SNOWFLAKE_WAREHOUSE')}
            TARGET_LAG = '1 minute'
            AS (
                SELECT id, {text_column}, metadata
                FROM {table_name}
            );
            """
            self.session.sql(sql).collect()
            return True
        except Exception as e:
            print(f"Error creating Cortex Search index: {e}")
            return False

    def search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search using Cortex Search"""
        if not self.session:
            self.connect()

        k = top_k or self.config.top_k

        try:
            sql = f"""
            SELECT id, text, metadata,
                   VECTOR_COSINE_SIMILARITY(
                       SNOWFLAKE.CORTEX.EMBED_TEXT_768('{self.config.embedding_model}', text),
                       SNOWFLAKE.CORTEX.EMBED_TEXT_768('{self.config.embedding_model}', '{query}')
                   ) as similarity
            FROM {self.config.index_name}
            ORDER BY similarity DESC
            LIMIT {k}
            """
            results = self.session.sql(sql).to_pandas()
            return results.to_dict('records')
        except Exception as e:
            print(f"Search error: {e}")
            return []


class LocalVectorSearch:
    """Local vector search using FAISS or ChromaDB"""

    def __init__(self, config: VectorSearchConfig):
        self.config = config
        self.index = None
        self.documents = []

    def connect(self):
        """Initialize local vector store"""
        try:
            import chromadb
            from chromadb.config import Settings

            self.client = chromadb.Client(Settings(
                persist_directory=f"./chroma_db/{self.config.index_name}"
            ))
            self.collection = self.client.get_or_create_collection(
                name=self.config.index_name,
                metadata={"dimension": self.config.dimension}
            )
            return True
        except ImportError:
            print("ChromaDB not installed. Install: pip install chromadb")
            return False
        except Exception as e:
            print(f"Local vector store error: {e}")
            return False

    def ingest_documents(self, documents: List[Dict[str, Any]]):
        """Ingest documents into local vector store"""
        if not self.collection:
            self.connect()

        try:
            ids = [doc.get("id", str(i)) for i, doc in enumerate(documents)]
            texts = [doc.get("text", "") for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]

            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            return True
        except Exception as e:
            print(f"Ingestion error: {e}")
            return False

    def search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search the local vector store"""
        if not self.collection:
            self.connect()

        k = top_k or self.config.top_k

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )

            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })

            return formatted_results
        except Exception as e:
            print(f"Search error: {e}")
            return []


class DocumentIngestion:
    """Handle document ingestion and chunking"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_file(self, file_path: str, file_type: str = None) -> List[Dict[str, Any]]:
        """Process a file and return chunked documents"""
        if file_type is None:
            file_type = Path(file_path).suffix.lower()

        # Route to appropriate processor
        if file_type in ['.txt', '.md']:
            return self._process_text_file(file_path)
        elif file_type in ['.pdf']:
            return self._process_pdf(file_path)
        elif file_type in ['.docx']:
            return self._process_docx(file_path)
        elif file_type in ['.csv']:
            return self._process_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _process_text_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Process text/markdown files"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        chunks = self._chunk_text(text)
        return [
            {
                "id": f"{Path(file_path).stem}_chunk_{i}",
                "text": chunk,
                "metadata": {
                    "source": file_path,
                    "chunk_index": i,
                    "file_type": "text"
                }
            }
            for i, chunk in enumerate(chunks)
        ]

    def _process_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Process PDF files"""
        try:
            import PyPDF2

            documents = []
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    chunks = self._chunk_text(text)

                    for chunk_idx, chunk in enumerate(chunks):
                        documents.append({
                            "id": f"{Path(file_path).stem}_page{page_num}_chunk{chunk_idx}",
                            "text": chunk,
                            "metadata": {
                                "source": file_path,
                                "page": page_num,
                                "chunk_index": chunk_idx,
                                "file_type": "pdf"
                            }
                        })

            return documents
        except ImportError:
            print("PyPDF2 not installed. Install: pip install PyPDF2")
            return []

    def _process_docx(self, file_path: str) -> List[Dict[str, Any]]:
        """Process Word documents"""
        try:
            from docx import Document

            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            chunks = self._chunk_text(text)

            return [
                {
                    "id": f"{Path(file_path).stem}_chunk_{i}",
                    "text": chunk,
                    "metadata": {
                        "source": file_path,
                        "chunk_index": i,
                        "file_type": "docx"
                    }
                }
                for i, chunk in enumerate(chunks)
            ]
        except ImportError:
            print("python-docx not installed. Install: pip install python-docx")
            return []

    def _process_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Process CSV files"""
        import pandas as pd

        df = pd.read_csv(file_path)
        documents = []

        for idx, row in df.iterrows():
            text = " | ".join([f"{col}: {val}" for col, val in row.items()])
            documents.append({
                "id": f"{Path(file_path).stem}_row_{idx}",
                "text": text,
                "metadata": {
                    "source": file_path,
                    "row_index": idx,
                    "file_type": "csv"
                }
            })

        return documents

    def _chunk_text(self, text: str) -> List[str]:
        """Chunk text into smaller pieces"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)

                if break_point > self.chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - self.chunk_overlap

        return [c for c in chunks if c]


def get_vector_search(config: VectorSearchConfig):
    """Factory function to get appropriate vector search implementation"""
    if config.provider == "databricks":
        return DatabricksVectorSearch(config)
    elif config.provider == "snowflake":
        return SnowflakeCortexSearch(config)
    elif config.provider == "local":
        return LocalVectorSearch(config)
    else:
        raise ValueError(f"Unsupported vector search provider: {config.provider}")


class RAGTool:
    """Retrieval-Augmented Generation tool for agents"""

    def __init__(self, vector_config: VectorSearchConfig):
        self.config = vector_config
        self.vector_search = get_vector_search(vector_config)
        self.vector_search.connect()

    def retrieve_context(self, query: str, top_k: int = None) -> str:
        """Retrieve relevant context for a query"""
        results = self.vector_search.search(query, top_k)

        if not results:
            return "No relevant context found."

        # Format context
        context_parts = []
        for i, result in enumerate(results, 1):
            text = result.get('text', result.get('documents', ''))
            metadata = result.get('metadata', {})
            source = metadata.get('source', 'Unknown')

            context_parts.append(f"[{i}] Source: {source}\n{text}\n")

        return "\n".join(context_parts)

    def answer_with_context(self, query: str, llm_response_func) -> str:
        """Get LLM answer with retrieved context"""
        context = self.retrieve_context(query)

        prompt = f"""Use the following context to answer the question. If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {query}

Answer:"""

        return llm_response_func(prompt)
