from langchain_chroma import Chroma
from app.core.config import settings
from app.services.llm_factory import LLMFactory

def get_vector_store():
    embeddings = LLMFactory.create_embeddings()
    return Chroma(
        persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
        embedding_function=embeddings,
        collection_name="confluence_docs"
    )
