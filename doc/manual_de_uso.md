# Manual de Uso y Pruebas - RAG Agent Microservice

Este documento detalla los pasos para levantar el servicio localmente y cómo probar los endpoints principales (Ingesta y Chat).

## 1. Prerrequisitos

Asegúrate de tener un entorno virtual configurado y las dependencias instaladas:

```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

Verifica que el archivo `.env` tenga las claves configuradas correctamente:

- `API_KEY`: La clave de seguridad para las peticiones (Header `X-API-KEY`).
- `OPENAI_API_KEY` o `GOOGLE_API_KEY`.
- Credenciales de Confluence (`CONFLUENCE_URL`, `CONFLUENCE_USERNAME`, `CONFLUENCE_API_TOKEN`).

## 2. Iniciar el Servidor

Ejecuta el siguiente comando en la raíz del proyecto para levantar el servidor de desarrollo:

```bash
uvicorn app.main:app --reload
```

El servidor estará corriendo en: `http://localhost:8000`.

Puedes acceder a la documentación interactiva (Swagger UI) en:

- [http://localhost:8000/docs](http://localhost:8000/docs)

## 3. Probar Endpoints con `curl`

A continuación, ejemplos para probar los endpoints desde la terminal. Asegúrate de reemplazar `TU_API_KEY` por el valor real que tengas en tu archivo `.env`.

### A. Ingesta de Datos (Indexing)

Este endpoint descarga páginas de Confluence y las guarda en la base de datos vectorial local.

- **Endpoint**: `POST /api/v1/ingest`
- **Header**: `X-API-KEY`

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "X-API-KEY: Z9gAWAb61kBapfmuHUvbZM4wmoZJLxkhWWyhUKZMeiM" \
  -H "Content-Type: application/json" \
  -d '{
    "space_key": "DS",
    "limit": 10
  }'
```

_(Nota: Reemplaza `"DS"` con la Key del espacio de Confluence real que quieras indexar)._

### B. Chat (Query)

Este endpoint recibe una pregunta, busca contexto en la base de datos y genera una respuesta con el LLM.

- **Endpoint**: `POST /api/v1/chat`
- **Header**: `X-API-KEY`

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "X-API-KEY: Z9gAWAb61kBapfmuHUvbZM4wmoZJLxkhWWyhUKZMeiM" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cómo configuro mi correo electrónico?",
    "history": []
  }'
```

## 4. Solución de Problemas Comunes

- **Error 500 en Ingesta**: Verifica que `lxml` esté instalado y que las credenciales de Confluence en `.env` sean correctas (el API Token debe ser válido).
- **Error 403 Forbidden**: Verifica que el header `X-API-KEY` coincida exactamente con lo que tienes en `.env`.
- **LangChain/Pydantic Error**: Asegúrate de estar usando una versión de Python compatible (3.10 - 3.12) y no la 3.14 (experimental).
