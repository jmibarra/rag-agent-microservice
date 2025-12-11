from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

class LLMFactory:
    @staticmethod
    def create_llm():
        if settings.LLM_PROVIDER == "gemini":
            if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is not set")
            return ChatGoogleGenerativeAI(
                model="gemini-pro", 
                google_api_key=settings.GOOGLE_API_KEY, 
                convert_system_message_to_human=True
            )
        else:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set")
            return ChatOpenAI(
                model_name="gpt-3.5-turbo", # Or gpt-4
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0
            )

    @staticmethod
    def create_embeddings():
        if settings.LLM_PROVIDER == "gemini":
             from langchain_google_genai import GoogleGenerativeAIEmbeddings
             if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is not set")
             return GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=settings.GOOGLE_API_KEY)
        else:
            from langchain_openai import OpenAIEmbeddings
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set")
            return OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
