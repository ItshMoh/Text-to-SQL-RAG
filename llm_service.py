import requests
import json
import config
import os # Import os to check if API key is set

# Base URL for Gemini API (generateContent endpoint)
# Note: The model name is part of the URL path
GEMINI_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# Base URL for Gemini API (embedContent endpoint)
GEMINI_EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"

# Choose model names (as strings now)
GEN_MODEL_NAME = 'gemini-2.0-flash' # Or 'gemini-1.5-flash-latest', 'gemini-1.5-pro-latest', etc.
EMBEDDING_MODEL_NAME = 'embedding-001' # The standard embedding model name

# --- Helper function to make the API call ---
def _call_gemini_api(url: str, data: dict) -> dict | None:
    """Helper to make POST request to Gemini API and handle basic errors."""
    if not config.GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY not found. Cannot call Gemini API.")
        return None

    # Add API key to the URL as per the curl example
    full_url = f"{url}?key={config.GOOGLE_API_KEY}"

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        # Use json=data directly with requests, it handles serialization
        response = requests.post(full_url, headers=headers, json=data)

        # Check for successful response status code
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Status Code: {e.response.status_code}")
             try:
                 print(f"Response Body: {e.response.json()}")
             except json.JSONDecodeError:
                 print(f"Response Body: {e.response.text}")
        return None
    except json.JSONDecodeError:
        print("API response was not valid JSON.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during API call: {e}")
        return None

# --- SQL Generation Function ---
def generate_sql(user_query: str, semantic_layer_text: str) -> str | None:
    """
    Generates an SQL query using the Gemini API.
    Passes the semantic_layer_text (formatted JSON) directly in the prompt.
    """
    prompt = f"""
You are a highly skilled AI assistant that translates natural language questions into SQL queries.
Use the provided database schema description below to write a valid SQLite query.
Pay close attention to table names, column names, data types, and relationships implied by the descriptions.
Map human-friendly terms to technical names using the provided semantic context and descriptions.
If a column has a value mapping (e.g., state codes), use the technical code in the WHERE clause.
Ensure the query is correct SQLite syntax.
Return only the SQL query, nothing else.

Database Schema Description:
{semantic_layer_text}

User Question:
{user_query}

SQL Query:
"""

    api_url = GEMINI_GENERATE_URL.format(model=GEN_MODEL_NAME)
    request_body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
        # Add generation configuration like temperature, max_output_tokens if needed
        # "generationConfig": {
        #     "temperature": 0.1,
        #     "maxOutputTokens": 200
        # }
    }

    response_json = _call_gemini_api(api_url, request_body)

    if response_json and 'candidates' in response_json:
        try:
            generated_sql = response_json['candidates'][0]['content']['parts'][0]['text']
            # Clean up potential markdown or extra text
            generated_sql = generated_sql.strip()
            # Remove markdown code block if present
            if generated_sql.startswith("```sql"):
                 generated_sql = generated_sql[6:].strip()
            if generated_sql.endswith("```"):
                 generated_sql = generated_sql[:-3].strip()

            print(f"Generated SQL: {generated_sql}")
            return generated_sql
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error parsing SQL generation response structure: {e}")
            print(f"Full Response: {json.dumps(response_json, indent=2)}")
            return None
    elif response_json and 'promptFeedback' in response_json:
         safety_ratings = response_json.get('promptFeedback', {}).get('safetyRatings')
         print(f"SQL generation blocked by safety filters: {safety_ratings}")
         return None
    else:
        print("SQL generation failed: No valid response received.")
        print(f"Full Response: {json.dumps(response_json, indent=2)}")
        return None


# --- Answer Generation Function ---
def generate_answer(user_query: str, retrieved_data: str) -> str | None:
    """
    Generates a natural language answer using the Gemini API based on
    the original user query and retrieved data.
    """
    prompt = f"""
You are an AI assistant helping a user understand data.
The user asked the following question: "{user_query}"
You have retrieved the following relevant data:
---
{retrieved_data}
---
Based on the user's question and the provided data, synthesize a clear and concise natural language answer.
If the data is empty or irrelevant, state that you could not find relevant information related to the question in the provided data.
Do not include the SQL query, table names, column names, or other technical database details in the final answer.
Present the information in a user-friendly way.
"""

    api_url = GEMINI_GENERATE_URL.format(model=GEN_MODEL_NAME)
    request_body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
         # Add generation configuration like temperature
        # "generationConfig": {
        #     "temperature": 0.5
        # }
    }

    response_json = _call_gemini_api(api_url, request_body)

    if response_json and 'candidates' in response_json:
        try:
            answer = response_json['candidates'][0]['content']['parts'][0]['text']
            print(f"Generated Answer: {answer}")
            return answer.strip()
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error parsing answer generation response structure: {e}")
            print(f"Full Response: {json.dumps(response_json, indent=2)}")
            return "Could not generate an answer due to a processing error."
    elif response_json and 'promptFeedback' in response_json:
         safety_ratings = response_json.get('promptFeedback', {}).get('safetyRatings')
         print(f"Answer generation blocked by safety filters: {safety_ratings}")
         return "Could not generate an answer (possibly blocked by safety filters)."
    else:
        print("Answer generation failed: No valid response received.")
        print(f"Full Response: {json.dumps(response_json, indent=2)}")
        return "Could not generate a final answer."


# --- Embedding Function ---
# This uses the embedContent endpoint, structure is slightly different
def embed_text(text: str):
    """Generates embedding for the given text using the Gemini API."""
    if not text or not text.strip():
        # print("Warning: Attempted to embed empty or whitespace text.")
        return None # Cannot embed empty text

    api_url = GEMINI_EMBED_URL.format(model=EMBEDDING_MODEL_NAME)
    request_body = {
        # The embedding API expects 'content' directly, potentially with parts
        "content": {
            "parts": [
                {"text": text}
            ]
        }
        # No need for 'model' in the body if it's in the URL path for the singular endpoint
        # "model": EMBEDDING_MODEL_NAME # Only needed for batchEmbedContents or if model not in URL
    }

    response_json = _call_gemini_api(api_url, request_body)

    if response_json and 'embedding' in response_json:
        try:
            embedding_values = response_json['embedding']['values']
            # print(f"Generated embedding of size: {len(embedding_values)}") # Optional debug
            return embedding_values # This should be a list of floats
        except (KeyError, TypeError) as e:
            print(f"Error parsing embedding response structure: {e}")
            print(f"Full Response: {json.dumps(response_json, indent=2)}")
            return None
    else:
        print("Embedding generation failed: No valid response received.")
        print(f"Full Response: {json.dumps(response_json, indent=2)}")
        return None