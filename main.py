import config
import semantic_layer
import database_service
import llm_service
import vector_db_service
import uuid # To generate unique IDs for queries

def main():
    print("Text-to-SQL RAG Chatbot Backend (Terminal Interface)")
    print("-" * 40)

    # 1. Load Semantic Layer
    semantic_config = semantic_layer.load_semantic_layer()
    if not semantic_config:
        print("Failed to load semantic layer. Exiting.")
        return

    # Format semantic layer for the LLM prompt
    semantic_layer_text_for_llm = semantic_layer.format_semantic_layer_for_prompt(semantic_config)
    # print("\n--- Semantic Layer Context Sent to LLM ---")
    # print(semantic_layer_text_for_llm) # Optional: Print the context being sent
    # print("------------------------------------------\n")


    # Ensure vector DB is initialized (it's done on import in vector_db_service)
    if not vector_db_service.collection:
         print("Failed to initialize Vector Database. Exiting.")
         return

    print("Semantic layer and Vector DB initialized. Ready to answer questions.")
    print("Type 'quit' or 'exit' to end the session.")

    # 2. Start the chat loop
    while True:
        user_query = input("\nAsk a question: ")
        if user_query.lower() in ['quit', 'exit']:
            break

        if not user_query.strip():
            print("Please enter a question.")
            continue

        # Generate a unique ID for this query sequence
        query_sequence_id = str(uuid.uuid4())
        print(f"Processing query (ID: {query_sequence_id})...")

        # --- Step 1: Generate SQL ---
        sql_query = llm_service.generate_sql(user_query, semantic_layer_text_for_llm)

        if not sql_query:
            print("Could not generate SQL query.")
            continue

        # --- Step 2: Execute SQL ---
        # Validate SQL (basic check)
        if not sql_query.strip().lower().startswith(("select", "with")):
             print("Generated text does not appear to be a SELECT or WITH SQL query. Aborting execution.")
             continue

        results, column_names, db_error = database_service.execute_sql_query(sql_query)

        if db_error:
            print(f"Error executing SQL query: {db_error}")
            # Optionally, you could try to refine the query with the LLM here
            continue

        if results is None: # Indicates an execution error occurred, even if db_error is None (shouldn't happen with current code but defensive)
             print("SQL query execution failed.")
             continue

        if not results:
             print("SQL query executed successfully, but returned no results.")
             # Even with no results, we might add this fact to vector DB or just proceed to answer generation
             # Let's proceed, the answer generation step will handle empty data.

        # --- Step 3: Store Fetched Data in Vector Database ---
        # Note: Storing raw SQL results directly in Vector DB for RAG Answer Gen
        # is a specific approach you requested. More typical is to store
        # documentation/prior Q&A etc.
        vector_db_service.add_results_to_vector_db(results, column_names, query_sequence_id)

        # --- Step 4: Retrieve Relevant Data from Vector Database (based on user query) ---
        # This step retrieves chunks from the *just added* results (or potentially past results)
        # that are most relevant to the *original user query*.
        retrieved_data_docs = vector_db_service.retrieve_data_from_vector_db(user_query, n_results=5) # Retrieve top 5 chunks

        if not retrieved_data_docs:
             print("Could not retrieve relevant data from the vector store for answering.")
             # You might choose to skip answer generation or generate a "no data found" answer
             retrieved_data_text = "No relevant data found."
        else:
            # Combine retrieved document texts into a single string for the LLM
            retrieved_data_text = "\n".join(retrieved_data_docs)
            print("\n--- Data Retrieved for Answering ---")
            print(retrieved_data_text)
            print("------------------------------------\n")


        # --- Step 5: Generate Natural Language Answer ---
        final_answer = llm_service.generate_answer(user_query, retrieved_data_text)

        if final_answer:
            print("\nAnswer:")
            print(final_answer)
        else:
            print("\nCould not generate a final answer.")

    print("\nExiting chatbot. Goodbye!")

if __name__ == "__main__":
    main()