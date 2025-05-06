import sqlite3
import config

def execute_sql_query(sql_query: str):
    """Executes a given SQL query against the database and returns results."""
    conn = None
    results = []
    column_names = []
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        column_names = [description[0] for description in cursor.description] if cursor.description else []
        print(f"Executed SQL: {sql_query}")
        # print(f"Results: {results}") # Optional: print results for debugging
    except sqlite3.Error as e:
        print(f"Database error executing query: {e}")
        print(f"SQL Query: {sql_query}")
        return None, None, f"Database Error: {e}" # Return error message
    except Exception as e:
        print(f"An unexpected error occurred during database execution: {e}")
        print(f"SQL Query: {sql_query}")
        return None, None, f"Execution Error: {e}" # Return error message
    finally:
        if conn:
            conn.close()
    return results, column_names, None # Return results, columns, no error