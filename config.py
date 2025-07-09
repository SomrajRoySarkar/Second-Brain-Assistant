import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cohere API Configuration
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "second_brain.db")

# Conversation Settings
MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", 50))
MAX_MEMORY_ENTRIES = int(os.getenv("MAX_MEMORY_ENTRIES", 1000))

# Knowledge Base Settings
KNOWLEDGE_FILE = os.getenv("KNOWLEDGE_FILE", "knowledge_base.json") 
