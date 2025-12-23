# Diseño de Solución - Microservicio Agente RAG

## Descripción del Objetivo

Desarrollar un microservicio API RAG (Generación Aumentada por Recuperación) para servir como backend de un agente de soporte al cliente. Procesará prompts desde una aplicación de Atlassian Forge, consultará una base de conocimientos en Confluence y generará respuestas utilizando LLMs configurables (ChatGPT o Gemini).

## Stack Tecnológico y Justificación

**Core**

- **Lenguaje**: Python 3.10+
  - _Por qué_: Estándar de la industria para IA/ML, vasto ecosistema de librerías.
- **Framework Web**: FastAPI
  - _Por qué_: Moderno, alto rendimiento, soporte nativo asíncrono (crítico para llamadas de bloqueo de E/S de LLM) y generación automática de OpenAPI (Swagger), esencial para la integración con Atlassian Forge.

**IA y RAG**

- **Orquestación**: LangChain
  - _Por qué_: Simplifica el cambio entre modelos (OpenAI vs Gemini), proporciona cargadores nativos para Confluence y utilidades para construir cadenas RAG.
- **Base de Datos Vectorial**: ChromaDB (Local)
  - _Por qué_: Código abierto, fácil de configurar localmente dentro del microservicio sin infraestructura compleja. Puede migrarse a Pinecone/Weaviate si se necesita escalar.
- **LLMs**:
  - OpenAI (gpt-3.5-turbo / gpt-4)
  - Google Gemini (gemini-pro)
  - _Configuración_: Gestionada mediante Variable de Entorno (`LLM_PROVIDER=openai|gemini`).

**Integración**

- **Confluence**: API REST de Atlassian vía `ConfluenceLoader` de LangChain.
  - _Requiere_: URL de la instancia, Nombre de usuario y Token de API.

## Arquitectura

El sistema implementa dos flujos principales:

### 1. Flujo de Ingesta (Indexación)

_Disparador_: Endpoint administrativo o tarea programada (cron job).

1.  **Conectar**: Autenticarse con Confluence.
2.  **Cargar**: Descargar páginas de espacios específicos.
3.  **Dividir**: Fragmentar el texto en partes manejables.
4.  **Incrustar (Embed)**: Generar incrustaciones vectoriales para los fragmentos.
5.  **Almacenar**: Persistir fragmentos e incrustaciones en ChromaDB en disco.

### 2. Flujo de Chat (Consulta)

_Disparador_: `POST /api/v1/chat` (desde Forge).
_Entrada_: `{ "message": "...", "history": [...] }`

1.  **Recibir**: Aceptar el prompt del usuario.
2.  **Incrustar (Embed)**: Generar incrustación para la consulta.
3.  **Recuperar**: Buscar fragmentos de contexto relevantes en ChromaDB.
4.  **Generar**: Construir el prompt con el contexto recuperado y enviarlo al LLM seleccionado.
5.  **Responder**: Devolver la respuesta generada.

### 3. Flujo de Webhook (WhatsApp)

_Disparador_: `POST /api/v1/webhook` (desde Twilio).

1.  **Validar**: Verificar firma `X-Twilio-Signature` contra `TWILIO_AUTH_TOKEN`.
2.  **Procesar**: Extraer cuerpo del mensaje y remitente.
3.  **Consultar**: Invocar lógica de RAG (`generate_response`).
4.  **Responder**: Devolver TwiML (XML) con la respuesta para WhatsApp/SMS.

## Estructura del Proyecto

```text
/rag-microservice
  /app
    /api
      __init__.py
      routes.py       # Endpoints de Chat e Ingesta
      deps.py         # Dependencias (auth, db)
    /core
      __init__.py
      config.py       # Configuraciones Pydantic (Variables de entorno)
      security.py     # Validación de API Key
    /services
      __init__.py
      llm_factory.py  # Lógica del Proveedor de LLM
      rag_service.py  # Lógica principal RAG (Recuperar + Generar)
      ingestion.py    # Carga e indexación de Confluence
    main.py           # Punto de entrada de la aplicación FastAPI
  /data               # Almacenamiento ChromaDB (Persistente)
  /doc
    solution_design.md
  .env                # Secretos
  requirements.txt
```

## Configuración y Seguridad

**Variables de Entorno Requeridas**:

- `OPENAI_API_KEY`, `GOOGLE_API_KEY`
- `CONFLUENCE_URL`, `CONFLUENCE_USERNAME`, `CONFLUENCE_API_TOKEN`
- `LLM_PROVIDER` (por defecto: openai)
- `TWILIO_AUTH_TOKEN` (para validación de webhooks)
- `CHROMA_PERSIST_DIRECTORY` (por defecto: data/chroma)

**Decisiones de Seguridad**:

- **Autenticación**: API Key simple (`X-API-KEY`) para validar solicitudes desde la aplicación Forge.
- **Persistencia**: ChromaDB está configurado para almacenar datos de forma persistente en el disco del servidor (`/data`), asegurando la retención del conocimiento entre reinicios.
