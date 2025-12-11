from langchain_community.document_loaders import ConfluenceLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import settings
from app.services.vector_store import get_vector_store

def ingest_confluence(space_key: str, limit: int = 50):
    if not settings.CONFLUENCE_URL or not settings.CONFLUENCE_USERNAME or not settings.CONFLUENCE_API_TOKEN:
        raise ValueError("Confluence credentials are not set")

    loader = ConfluenceLoader(
        url=settings.CONFLUENCE_URL,
        username=settings.CONFLUENCE_USERNAME,
        api_key=settings.CONFLUENCE_API_TOKEN
    )
    # load pages
    documents = loader.load(space_key=space_key, limit=limit, include_attachments=False)
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    
    vector_store = get_vector_store()
    vector_store.add_documents(texts)
    vector_store.persist()
    
    return {"status": "success", "documents_processed": len(documents), "chunks_created": len(texts)}
