import sys
import os
import shutil

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.services.ingestion import ingest_confluence

def reset_and_ingest():
    # 1. Clear existing database
    persist_dir = settings.CHROMA_PERSIST_DIRECTORY
    print(f"Checking for existing vector store at: {persist_dir}")
    if os.path.exists(persist_dir):
        print("Removing existing vector store data (to fix embedding mismatch)...")
        shutil.rmtree(persist_dir)
        print("Cleaned.")
    else:
        print("No existing vector store found.")

    # 2. Run ingestion
    print("\nStarting ingestion from Confluence...")
    # NOTE: You mentioned 'AC' as space_key in logs, using 'DS' or similar as default or input matches user intent
    # The logs showed space_key='AC'. I will try that default or maybe just 'DS' if AC fails?
    # Let's use a standard default or ask.
    # Actually, the user's previous successful run likely used a specific key.
    # I'll default to 'AC' since that was in the logs of Step 175.
    space_key_to_use = "AC" 
    
    try:
        result = ingest_confluence(space_key=space_key_to_use, limit=50)
        print("\nIngestion Result:")
        print(result)
        print("\nSUCCESS: Data re-ingested with new embeddings.")
    except Exception as e:
        print(f"\nFAILURE during ingestion: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reset_and_ingest()
