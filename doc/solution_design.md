# Solution Design - RAG Agent Microservice

## Goal Description

Develop a RAG (Retrieval-Augmented Generation) microservice API to serve as a backend for a customer support agent. It will process prompts from an Atlassian Forge app, consult a Confluence knowledge base, and generate responses using configurable LLMs (ChatGPT or Gemini).

## Tech Stack

- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Orchestration**: LangChain
- **Vector DB**: ChromaDB (Persistent)
- **LLMs**: OpenAI (gpt-3.5/4) & Google Gemini (gemini-pro)
- **Integration**: Atlassian Confluence via LangChain

## Architecture & Security

- **Security**: A simple API Key (`X-API-KEY` header) will be used for authentication.
- **Persistence**: ChromaDB will store data persistently on the disk (`/data`), not in memory.

## Project Structure

```text
/rag-microservice
  /app
    /api
      __init__.py
      routes.py       # Chat and Ingestion endpoints
      deps.py         # Dependencies (auth, db)
    /core
      __init__.py
      config.py       # Pydantic settings (Env vars)
      security.py     # API Key validation
    /services
      __init__.py
      llm_factory.py  # LLM Provider logic
      rag_service.py  # Main RAG logic (Retrieve + Generate)
      ingestion.py    # Confluence loading & indexing
    main.py           # FastAPI app entrypoint
  /data               # ChromaDB storage
  .env                # Secrets
  requirements.txt
```

## Dependencies

- `fastapi`, `uvicorn`
- `langchain`, `langchain-openai`, `langchain-google-genai`, `langchain-community`
- `chromadb`
- `atlassian-python-api` (for Confluence loader)
- `pydantic-settings`
- `python-dotenv`
- `tiktoken`
- `beautifulsoup4`, `lxml`

## Endpoints

1.  **`POST /api/v1/ingest`**: Triggers ingestion from Confluence.
    - Body: `{"space_key": "KEY", "limit": 10}`
2.  **`POST /api/v1/chat`**: Sends a query and checks for a response.
    - Body: `{"message": "Question?", "history": []}`
