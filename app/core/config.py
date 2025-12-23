from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    # App
    APP_NAME: str = "RAG Agent Microservice"
    API_V1_STR: str = "/api/v1"
    
    # LLM
    OPENAI_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    LLM_PROVIDER: str = "openai" # openai or gemini

    # Confluence
    CONFLUENCE_URL: str | None = None
    CONFLUENCE_USERNAME: str | None = None
    CONFLUENCE_API_TOKEN: str | None = None

    # Security
    API_KEY: str
    TWILIO_AUTH_TOKEN: str | None = None

    # Vector DB
    CHROMA_PERSIST_DIRECTORY: str = "data/chroma"

settings = Settings()
