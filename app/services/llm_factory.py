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
                # A veces ayuda poner el prefijo 'models/' explícitamente
                model="gemini-2.0-flash", 
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0,
                max_retries=2,
            )
        else:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set")
            return ChatOpenAI(
                model_name="gpt-3.5-turbo", 
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0
            )

    @staticmethod
    def create_embeddings():
        if settings.LLM_PROVIDER == "gemini":
             from langchain_google_genai import GoogleGenerativeAIEmbeddings
             if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is not set")
             
             # Aseguramos usar el modelo de embeddings correcto
             return GoogleGenerativeAIEmbeddings(
                 model="models/text-embedding-004", # 'embedding-001' es legacy, el 004 es mejor y más barato
                 google_api_key=settings.GOOGLE_API_KEY
             )
        else:
            from langchain_openai import OpenAIEmbeddings
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set")
            return OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)