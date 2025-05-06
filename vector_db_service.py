import chromadb
from chromadb.utils import embedding_functions
import config
import llm_service # To use the embedding model defined there

# Use the embedding function corresponding to the Gemini model
# Chroma can use Google's embedding API directly if configured.
# For this example, we'll generate embeddings via llm_service and pass them.
# A more direct way if Chroma supports the specific Gemini embedding model:
# google_ef = embedding_functions.GoogleEmbeddingFunction(api_key=config.GOOGLE_API_KEY)
# For simplicity mirroring the llm_service, we'll generate manually for now.

client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)

try:
    # Get or create a collection
    # Note: Creating/getting collection requires an embedding function if you
    # want Chroma to handle embedding internally. If passing embeddings,
    # you might use a NullEmbeddingFunction or a specific one that matches yours.
    # Let's create without specifying one here, and pass embeddings directly.
    # If you want Chroma to embed, uncomment the line above and pass google_ef
    collection = client.get_or_create_collection(name="sql_results")

except Exception as e:
    print(f"Error initializing ChromaDB collection: {e}")
    collection = None # Indicate failure


def add_results_to_vector_db(results, column_names, query_id):
    """
    Adds SQL results to the vector database.
    Each row, potentially formatted with column names, becomes a document.
    """
    if not collection or not results or not column_names:
        print("No collection, results, or column names to add to vector DB.")
        return

    documents = []
    metadatas = []
    ids = []

    for i, row in enumerate(results):
        # Format row data with column names
        row_text = ", ".join([f"{col}: {val}" for col, val in zip(column_names, row)])
        document = f"SQL Result (Query ID: {query_id}, Row {i+1}): {row_text}"
        documents.append(document)
        metadatas.append({"query_id": query_id, "row_index": i})
        ids.append(f"query_{query_id}_row_{i}")

    # Generate embeddings for the documents
    embeddings = [llm_service.embed_text(doc) for doc in documents]
    # Filter out any failed embeddings
    valid_embeddings = [e for e in embeddings if e is not None]
    valid_documents = [d for d, e in zip(documents, embeddings) if e is not None]
    valid_metadatas = [m for m, e in zip(metadatas, embeddings) if e is not None]
    valid_ids = [id for id, e in zip(ids, embeddings) if e is not None]


    if valid_embeddings:
        try:
            collection.add(
                embeddings=valid_embeddings,
                documents=valid_documents,
                metadatas=valid_metadatas,
                ids=valid_ids
            )
            print(f"Added {len(valid_embeddings)} documents to vector DB for query ID {query_id}.")
        except Exception as e:
            print(f"Error adding documents to ChromaDB: {e}")
    else:
        print("No valid embeddings generated to add to vector DB.")


def retrieve_data_from_vector_db(query_text: str, n_results: int = 5):
    """
    Retrieves relevant data from the vector database based on a query.
    """
    if not collection:
        print("ChromaDB collection not initialized.")
        return []

    query_embedding = llm_service.embed_text(query_text)
    if not query_embedding:
        print("Failed to generate embedding for retrieval query.")
        return []

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
            # Optional: where_clause, include=['metadatas', 'documents', 'distances']
        )
        # The result structure is a bit nested, extract documents
        retrieved_documents = results.get('documents', [[]])[0] if results else []
        print(f"Retrieved {len(retrieved_documents)} documents from vector DB.")
        # print(f"Retrieved Docs: {retrieved_documents}") # Debugging
        return retrieved_documents

    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        return []