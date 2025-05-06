import os
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DATABASE_PATH = os.getenv("DATABASE_PATH")
SEMANTIC_LAYER_PATH = os.getenv("SEMANTIC_LAYER_PATH")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH")