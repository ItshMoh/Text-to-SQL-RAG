import json
import config

def load_semantic_layer(file_path: str = config.SEMANTIC_LAYER_PATH):
    """Loads the semantic layer configuration from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            semantic_config = json.load(f)
        print(f"Semantic layer loaded from {file_path}")
        return semantic_config
    except FileNotFoundError:
        print(f"Error: Semantic layer file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not parse semantic layer JSON from {file_path}")
        return None
    except Exception as e:
        print(f"An error occurred loading semantic layer: {e}")
        return None

# Helper to format semantic layer for LLM prompt
def format_semantic_layer_for_prompt(semantic_config):
    """Formats the semantic layer config into a string suitable for an LLM prompt."""
    if not semantic_config:
        return "No semantic layer available."

    formatted_string = "Database Schema Description:\n\n"
    db_info = semantic_config.get("database", {})
    formatted_string += f"Database Name: {db_info.get('technical_name', 'N/A')} ({db_info.get('human_name', 'N/A')})\n"
    formatted_string += f"Description: {db_info.get('description', 'N/A')}\n\n"

    tables = semantic_config.get("tables", [])
    for table in tables:
        formatted_string += f"Table: {table.get('technical_name', 'N/A')} ({', '.join(table.get('human_names', []))})\n"
        formatted_string += f"  Description: {table.get('description', 'N/A')}\n"
        formatted_string += "  Columns:\n"
        columns = table.get("columns", [])
        for column in columns:
            formatted_string += f"    - {column.get('technical_name', 'N/A')} ({', '.join(column.get('human_names', []))})\n"
            formatted_string += f"      Type: {column.get('data_type', 'N/A')}\n"
            formatted_string += f"      Description: {column.get('description', 'N/A')}\n"
            if column.get("value_map"):
                 formatted_string += f"      Value Mapping: {json.dumps(column['value_map'])}\n" # Include value map
        formatted_string += "\n" # Spacer between tables

    # You could add relationships here if defined in your JSON
    # For this simple example, we rely on the LLM understanding FKs from descriptions/column names

    return formatted_string