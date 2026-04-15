import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.rag_service import generate_response
print("RAG Service imported successfully")
