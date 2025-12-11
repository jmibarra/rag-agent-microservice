Objetivo
Desarrollar un microservicio API que sirva como backend para un agente de atención al cliente. Este servicio procesará prompts de usuarios (provenientes de una app Atlassian Forge), consultará una base de conocimientos en Confluence y generará respuestas utilizando modelos LLM configurables (ChatGPT o Gemini).

Stack Tecnológico Propuesto
Core
Lenguaje: Python 3.10+

Por qué: Estándar de industria para AI/ML, gran ecosistema de librerías.

Framework Web: FastAPI

Por qué: Moderno, rápido, soporte nativo asíncrono (crítico para llamadas LLM), y genera automáticamente la documentación OpenAPI (Swagger) que Atlassian Forge necesitará para conectarse.

AI & RAG
Orquestación: LangChain

Por qué: Facilita el cambio entre modelos (OpenAI vs Google), tiene cargadores nativos para Confluence y utilidades para cadenas RAG.

Base de Datos Vectorial: ChromaDB (Local)

Por qué: Open source, fácil de configurar localmente dentro del microservicio para empezar sin infraestructura extra compleja. Se puede migrar a Pinecone/Weaviate si escala.

Modelos (LLMs):

OpenAI (gpt-3.5-turbo / gpt-4)

Google Gemini (gemini-pro)

Configuración: Se gestionará vía Variables de Entorno (LLM_PROVIDER=openai|gemini).

Integración
Confluence: API REST de Atlassian via LangChain ConfluenceLoader.

Requiere: URL de la instancia, Username, y API Key.

Arquitectura de Alto Nivel
El sistema tendrá dos flujos principales:

1. Flujo de Ingesta (Indexing)
   Trigger: Endpoint administrativo o cron job.

Proceso:

Conectar a Confluence.

Descargar páginas de espacios específicos.

Dividir texto en "chunks" (fragmentos).

Generar embeddings (vectores) de estos fragmentos.

Guardar en ChromaDB.

2. Flujo de Chat (Query)
   Trigger: POST /api/v1/chat (desde Forge).

Input: { "message": "...", "history": [...] }

Proceso:

Recibir prompt.

Generar embedding de la consulta.

Buscar fragmentos relevantes en ChromaDB (Retrieval).

Construir prompt con contexto recuperado.

Enviar a LLM seleccionado (Gemini o ChatGPT).

Devolver respuesta generada.

Estructura de Directorios Propuesta

/rag-microservice
/app
/api # Endpoints (FastAPI routers)
/core # Config, logging, security
/services # Lógica de negocio
llm_factory.py # Selector de modelos
rag_service.py # Lógica RAG
ingestion.py # Lógica Confluence
main.py # Entrypoint
/data # Persistencia local de ChromaDB (si aplica)
.env # Secretos
requirements.txt
Configuración Requerida
Para que funcione, necesitaremos configurar:

API Keys: OPENAI_API_KEY, GOOGLE_API_KEY.

Atlassian: CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN.

Preguntas de Diseño
Persistencia: ¿Desea que la base de datos vectorial sea efímera (en memoria) o persistente en disco del servidor? (Recomendado: Persistente en disco).

Seguridad: El endpoint necesitará autenticación. ¿Podemos asumir una API Key simple (X-API-KEY) para validar las peticiones desde Forge?
