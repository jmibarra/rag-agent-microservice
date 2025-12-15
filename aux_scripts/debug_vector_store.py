import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

# Explicitly print start
print("Starting vector store check...", file=sys.stderr)

try:
    from app.services.vector_store import get_vector_store
    from app.core.config import settings

    print(f"Imported modules. Checking path: {settings.CHROMA_PERSIST_DIRECTORY}", file=sys.stderr)

    vs = get_vector_store()
    print("Got vector store object", file=sys.stderr)

    collection = vs._collection
    count = collection.count()
    
    print(f"---", file=sys.stderr)
    print(f"Total Documents in Collection '{collection.name}': {count}", file=sys.stderr)
    print(f"---", file=sys.stderr)

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"CRITICAL ERROR: {e}", file=sys.stderr)
