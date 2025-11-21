"""
Knowledge Base Management - Document Ingestion and Vector Search
Supports Snowflake (Stages + Cortex Search) and Databricks (Volumes + Vector Search)
"""
import streamlit as st
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui import load_custom_css, render_header, render_sidebar_section
from utils.vector_search import VectorSearchManager, VectorSearchConfig, DocumentIngestion
from config import get_platform_config

# Page configuration
st.set_page_config(
    page_title="Knowledge Base - Cortex AI",
    page_icon="📚",
    layout="wide"
)

# Load custom CSS
load_custom_css()

# Initialize session state
if "vector_manager" not in st.session_state:
    st.session_state.vector_manager = VectorSearchManager()
if "uploaded_files_buffer" not in st.session_state:
    st.session_state.uploaded_files_buffer = []

render_header("Knowledge Base", "Document Ingestion & Vector Search")

st.markdown("""
<div style="padding: 24px; max-width: 1400px; margin: 0 auto;">
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload Documents", "🔍 Vector Search Indexes", "📊 Manage Indexes", "⚙️ Configuration"])

# TAB 1: Upload Documents
with tab1:
    st.markdown("### Upload Documents to Knowledge Base")
    st.markdown("Upload documents to build your agent's knowledge base with RAG capabilities")
    st.markdown("<br>", unsafe_allow_html=True)

    # Get global platform configuration
    platform_config = get_platform_config()
    platform = platform_config.get_platform_name()

    # Show current platform
    st.markdown(f"""
    <div style="background: var(--sf-primary-light); border: 1px solid var(--sf-primary);
                border-radius: 8px; padding: 12px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 32px;">{platform_config.get_platform_icon()}</span>
            <div>
                <div style="font-weight: 600; font-size: 14px;">Deployment Platform: {platform}</div>
                <div style="font-size: 12px; color: var(--sf-text-muted);">
                    Storage: {platform_config.get_storage_label()} •
                    Search: {platform_config.get_vector_search_label()}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Platform-specific configuration
    if platform_config.is_snowflake():
        st.markdown("#### ❄️ Snowflake Configuration")

        col1, col2 = st.columns(2)
        with col1:
            stage_name = st.text_input(
                "Stage Name",
                placeholder="@MY_STAGE",
                help="Snowflake stage for document storage"
            )
            database = st.text_input(
                "Database",
                value=os.getenv("SNOWFLAKE_DATABASE", ""),
                placeholder="MY_DATABASE"
            )

        with col2:
            schema = st.text_input(
                "Schema",
                value=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
                placeholder="PUBLIC"
            )
            embedding_model = st.selectbox(
                "Cortex Embedding Model",
                options=platform_config.get_embedding_options(),
                help="Snowflake Cortex embedding model"
            )

        st.info("""
        **Snowflake Setup:**
        1. Documents will be uploaded to the specified Stage
        2. Cortex Search service will be created for vector search
        3. Embeddings generated using Snowflake Cortex
        """)

    elif platform_config.is_databricks():
        st.markdown("#### 🧱 Databricks Configuration")

        col1, col2 = st.columns(2)
        with col1:
            volume_path = st.text_input(
                "Volume Path",
                placeholder="/Volumes/catalog/schema/volume_name",
                help="Unity Catalog volume path for document storage"
            )
            catalog = st.text_input(
                "Catalog",
                value=os.getenv("DATABRICKS_CATALOG", "main"),
                placeholder="main"
            )

        with col2:
            endpoint_name = st.text_input(
                "Vector Search Endpoint",
                placeholder="my_endpoint",
                help="Databricks Vector Search endpoint name"
            )
            embedding_model = st.selectbox(
                "Embedding Model",
                options=platform_config.get_embedding_options(),
                help="Model for generating embeddings"
            )

        st.info("""
        **Databricks Setup:**
        1. Documents uploaded to Unity Catalog Volume
        2. Vector Search index created with specified endpoint
        3. Embeddings computed and stored in Delta table
        """)

    else:  # Local
        st.markdown("#### 💻 Local Development Configuration")

        col1, col2 = st.columns(2)
        with col1:
            local_storage = st.text_input(
                "Local Storage Path",
                value="./documents",
                help="Local directory for document storage"
            )

        with col2:
            embedding_model = st.selectbox(
                "Embedding Model",
                options=platform_config.get_embedding_options(),
                help="OpenAI embedding model for local vector store"
            )

        st.info("""
        **Local Setup:**
        1. Documents stored in local filesystem
        2. ChromaDB used for vector storage
        3. Embeddings via OpenAI API
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    # File Upload
    st.markdown("#### 📁 Upload Files")

    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=["txt", "md", "pdf", "docx", "csv"],
        accept_multiple_files=True,
        help="Supported formats: TXT, MD, PDF, DOCX, CSV"
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected:**")

        for file in uploaded_files:
            file_size = len(file.getvalue()) / 1024  # KB
            st.markdown(f"- {file.name} ({file_size:.1f} KB)")

        # Chunking configuration
        st.markdown("#### ⚙️ Chunking Configuration")
        col1, col2 = st.columns(2)

        with col1:
            chunk_size = st.number_input(
                "Chunk Size (characters)",
                min_value=100,
                max_value=5000,
                value=1000,
                step=100,
                help="Size of text chunks for embedding"
            )

        with col2:
            chunk_overlap = st.number_input(
                "Chunk Overlap (characters)",
                min_value=0,
                max_value=500,
                value=200,
                step=50,
                help="Overlap between consecutive chunks"
            )

        # Index selection
        existing_indexes = st.session_state.vector_manager.list_configs()

        if existing_indexes:
            index_options = {f"{idx.name} ({idx.provider})": idx.id for idx in existing_indexes}
            selected_index = st.selectbox(
                "Add to Existing Index",
                options=["Create New Index"] + list(index_options.keys())
            )
        else:
            selected_index = "Create New Index"
            st.info("No existing indexes. A new index will be created.")

        # New index name if creating
        if selected_index == "Create New Index":
            new_index_name = st.text_input(
                "New Index Name",
                placeholder="my_knowledge_base",
                help="Name for the new vector search index"
            )
        else:
            new_index_name = None

        st.markdown("<br>", unsafe_allow_html=True)

        # Process and upload button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🚀 Process & Upload", type="primary", use_container_width=True):
                if selected_index == "Create New Index" and not new_index_name:
                    st.error("Please provide a name for the new index")
                else:
                    with st.spinner("Processing documents..."):
                        try:
                            # Initialize document ingestion
                            ingestion = DocumentIngestion(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

                            # Process each file
                            all_documents = []
                            progress_bar = st.progress(0)

                            for idx, file in enumerate(uploaded_files):
                                # Save temp file
                                temp_path = f"./temp_{file.name}"
                                with open(temp_path, "wb") as f:
                                    f.write(file.getvalue())

                                # Process file
                                documents = ingestion.process_file(temp_path)
                                all_documents.extend(documents)

                                # Cleanup
                                os.remove(temp_path)

                                # Update progress
                                progress_bar.progress((idx + 1) / len(uploaded_files))

                            st.success(f"✅ Processed {len(all_documents)} chunks from {len(uploaded_files)} files")

                            # Create or use existing index
                            if selected_index == "Create New Index":
                                # Create new index
                                config_kwargs = {}

                                if platform_config.is_snowflake():
                                    config_kwargs = {
                                        "volume_path": f"{database}.{schema}.{stage_name}",
                                        "endpoint_name": f"{database}.{schema}.CORTEX_SEARCH_{new_index_name.upper()}"
                                    }
                                elif platform_config.is_databricks():
                                    config_kwargs = {
                                        "volume_path": volume_path,
                                        "endpoint_name": endpoint_name
                                    }
                                else:
                                    config_kwargs = {
                                        "volume_path": local_storage
                                    }

                                vector_config = st.session_state.vector_manager.create_index(
                                    name=new_index_name,
                                    provider=platform_config.platform.value,
                                    embedding_model=embedding_model,
                                    **config_kwargs
                                )

                                st.success(f"✅ Created new index: {new_index_name}")
                            else:
                                # Use existing index
                                vector_config = st.session_state.vector_manager.load_config(
                                    index_options[selected_index]
                                )

                            # Ingest documents
                            from utils.vector_search import get_vector_search

                            vector_search = get_vector_search(vector_config)
                            vector_search.connect()

                            if hasattr(vector_search, 'ingest_documents'):
                                vector_search.ingest_documents(all_documents)
                                st.success(f"✅ Ingested {len(all_documents)} document chunks into {vector_config.name}")
                            else:
                                st.warning("Document ingestion not yet implemented for this provider")

                            st.balloons()

                        except Exception as e:
                            st.error(f"Error processing documents: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())

        with col2:
            if st.button("Clear Files", use_container_width=True):
                st.rerun()

# TAB 2: Vector Search Indexes
with tab2:
    st.markdown("### Vector Search Indexes")
    st.markdown("Browse and search your knowledge base indexes")
    st.markdown("<br>", unsafe_allow_html=True)

    indexes = st.session_state.vector_manager.list_configs()

    if not indexes:
        st.info("No vector search indexes configured. Upload documents in the 'Upload Documents' tab to get started.")
    else:
        # Index selector
        index_options = {f"{idx.name} ({idx.provider})": idx for idx in indexes}
        selected = st.selectbox("Select Index", options=list(index_options.keys()))

        if selected:
            config = index_options[selected]

            # Display index info
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="sf-card">
                    <div class="sf-card-title">📊 Index Details</div>
                    <div style="margin-top: 12px; font-size: 13px;">
                        <div><strong>Name:</strong> {config.name}</div>
                        <div><strong>Provider:</strong> {config.provider}</div>
                        <div><strong>Model:</strong> {config.embedding_model}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="sf-card">
                    <div class="sf-card-title">⚙️ Configuration</div>
                    <div style="margin-top: 12px; font-size: 13px;">
                        <div><strong>Dimension:</strong> {config.dimension}</div>
                        <div><strong>Distance:</strong> {config.distance_metric}</div>
                        <div><strong>Top K:</strong> {config.top_k}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="sf-card">
                    <div class="sf-card-title">📁 Storage</div>
                    <div style="margin-top: 12px; font-size: 13px;">
                        <div><strong>Location:</strong> {config.volume_path or 'N/A'}</div>
                        <div><strong>Endpoint:</strong> {config.endpoint_name or 'N/A'}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Search interface
            st.markdown("#### 🔍 Test Search")

            query = st.text_input(
                "Search Query",
                placeholder="Enter your search query...",
                label_visibility="collapsed"
            )

            col1, col2 = st.columns([1, 4])
            with col1:
                top_k = st.number_input("Results", min_value=1, max_value=20, value=5)

            if query and st.button("Search", type="primary"):
                with st.spinner("Searching..."):
                    try:
                        from utils.vector_search import get_vector_search

                        vector_search = get_vector_search(config)
                        vector_search.connect()
                        results = vector_search.search(query, top_k=top_k)

                        if results:
                            st.markdown(f"**Found {len(results)} results:**")

                            for i, result in enumerate(results, 1):
                                text = result.get('text', result.get('documents', ''))
                                metadata = result.get('metadata', {})
                                distance = result.get('distance', result.get('similarity', 'N/A'))

                                with st.expander(f"Result {i} - Score: {distance}"):
                                    st.markdown(f"**Text:**\n{text}")
                                    st.markdown(f"**Metadata:** {metadata}")
                        else:
                            st.info("No results found")

                    except Exception as e:
                        st.error(f"Search error: {str(e)}")

# TAB 3: Manage Indexes
with tab3:
    st.markdown("### Manage Vector Search Indexes")
    st.markdown("View, edit, and delete your knowledge base indexes")
    st.markdown("<br>", unsafe_allow_html=True)

    indexes = st.session_state.vector_manager.list_configs()

    if not indexes:
        st.info("No indexes to manage")
    else:
        for config in indexes:
            st.markdown(f"""
            <div class="sf-card">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <div style="font-size: 40px;">🔍</div>
                    <div style="flex: 1;">
                        <div class="sf-card-title">{config.name}</div>
                        <div class="sf-card-description">
                            {config.provider.title()} • {config.embedding_model} • {config.index_name}
                        </div>
                        <div style="margin-top: 8px; font-size: 11px; color: var(--sf-text-muted);">
                            Volume: {config.volume_path or 'N/A'} • Endpoint: {config.endpoint_name or 'N/A'}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("📊 Stats", key=f"stats_{config.id}", use_container_width=True):
                    st.info("Statistics feature coming soon!")

            with col2:
                if st.button("🔄 Sync", key=f"sync_{config.id}", use_container_width=True):
                    st.info("Sync feature coming soon!")

            with col3:
                if st.button("📝 Edit", key=f"edit_{config.id}", use_container_width=True):
                    st.info("Edit feature coming soon!")

            with col4:
                if st.button("🗑️ Delete", key=f"delete_{config.id}", use_container_width=True):
                    st.session_state.vector_manager.delete_config(config.id)
                    st.success(f"Deleted index: {config.name}")
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

# TAB 4: Configuration
with tab4:
    st.markdown("### Platform Configuration")
    st.markdown("Configure connection settings for Snowflake and Databricks")
    st.markdown("<br>", unsafe_allow_html=True)

    config_tab1, config_tab2 = st.tabs(["❄️ Snowflake", "🧱 Databricks"])

    with config_tab1:
        st.markdown("#### Snowflake Configuration")

        col1, col2 = st.columns(2)

        with col1:
            st.text_input(
                "Account",
                value=os.getenv("SNOWFLAKE_ACCOUNT", ""),
                key="sf_account",
                help="Snowflake account identifier"
            )
            st.text_input(
                "User",
                value=os.getenv("SNOWFLAKE_USER", ""),
                key="sf_user"
            )
            st.text_input(
                "Database",
                value=os.getenv("SNOWFLAKE_DATABASE", ""),
                key="sf_database"
            )

        with col2:
            st.text_input(
                "Warehouse",
                value=os.getenv("SNOWFLAKE_WAREHOUSE", ""),
                key="sf_warehouse"
            )
            st.text_input(
                "Schema",
                value=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
                key="sf_schema"
            )
            st.text_input(
                "Role",
                value=os.getenv("SNOWFLAKE_ROLE", ""),
                key="sf_role"
            )

        st.markdown("**Available Stages:**")

        if st.button("🔍 List Stages", key="list_stages"):
            st.code("""
-- Create a stage for document storage
CREATE STAGE MY_DOCS_STAGE;

-- Upload files to stage
PUT file://path/to/document.pdf @MY_DOCS_STAGE;

-- List files in stage
LIST @MY_DOCS_STAGE;
            """, language="sql")

        st.markdown("**Cortex Search:**")
        st.code("""
-- Create Cortex Search service
CREATE CORTEX SEARCH SERVICE my_search_service
ON text_column
WAREHOUSE = COMPUTE_WH
TARGET_LAG = '1 minute'
AS (
    SELECT id, text_column, metadata
    FROM my_documents_table
);

-- Search using Cortex
SELECT * FROM TABLE(
    my_search_service.SEARCH(
        query => 'your search query',
        num_results => 5
    )
);
        """, language="sql")

    with config_tab2:
        st.markdown("#### Databricks Configuration")

        col1, col2 = st.columns(2)

        with col1:
            st.text_input(
                "Host",
                value=os.getenv("DATABRICKS_HOST", ""),
                key="db_host",
                help="Databricks workspace URL"
            )
            st.text_input(
                "HTTP Path",
                value=os.getenv("DATABRICKS_HTTP_PATH", ""),
                key="db_http_path"
            )
            st.text_input(
                "Catalog",
                value=os.getenv("DATABRICKS_CATALOG", "main"),
                key="db_catalog"
            )

        with col2:
            st.text_input(
                "Token",
                value="",
                type="password",
                key="db_token"
            )
            st.text_input(
                "Schema",
                value=os.getenv("DATABRICKS_SCHEMA", "default"),
                key="db_schema"
            )
            st.text_input(
                "Vector Search Endpoint",
                value="",
                key="db_vs_endpoint"
            )

        st.markdown("**Unity Catalog Volumes:**")

        if st.button("🔍 List Volumes", key="list_volumes"):
            st.code("""
-- Create a volume for document storage
CREATE VOLUME main.default.my_docs;

-- Upload files using Databricks CLI or UI
databricks fs cp local_file.pdf dbfs:/Volumes/main/default/my_docs/

-- List files
%fs ls /Volumes/main/default/my_docs/
            """, language="sql")

        st.markdown("**Vector Search:**")
        st.code("""
# Create vector search index
from databricks.vector_search.client import VectorSearchClient

client = VectorSearchClient()

# Create index
client.create_delta_sync_index(
    endpoint_name="my_endpoint",
    index_name="main.default.my_docs_index",
    source_table_name="main.default.my_docs_table",
    pipeline_type="TRIGGERED",
    primary_key="id",
    embedding_dimension=1536,
    embedding_vector_column="embedding"
)

# Search
index = client.get_index("main.default.my_docs_index")
results = index.similarity_search(
    query_text="your search query",
    columns=["id", "text"],
    num_results=5
)
        """, language="python")

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 0; border-bottom: 1px solid var(--sf-border); margin-bottom: 20px;">
        <div style="font-weight: 600; font-size: 16px;">Knowledge Base</div>
        <div style="font-size: 12px; color: var(--sf-text-muted);">RAG & Vector Search</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 Quick Stats")

    indexes = st.session_state.vector_manager.list_configs()

    st.metric("Total Indexes", len(indexes))

    if indexes:
        by_provider = {}
        for idx in indexes:
            by_provider[idx.provider] = by_provider.get(idx.provider, 0) + 1

        for provider, count in by_provider.items():
            st.metric(f"{provider.title()} Indexes", count)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🎯 Supported Platforms")

    st.markdown("""
    **Snowflake:**
    - Stages for storage
    - Cortex Search
    - Cortex embeddings

    **Databricks:**
    - Unity Catalog Volumes
    - Vector Search
    - Custom embeddings

    **Local:**
    - File system storage
    - ChromaDB
    - OpenAI embeddings
    """)

st.markdown("</div>", unsafe_allow_html=True)
