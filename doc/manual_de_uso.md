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
- `TWILIO_AUTH_TOKEN`: Token de autenticación de Twilio para validar webhooks.
- Parametría para clientes de Jira Service Management (`JSM_CLOUD_ID`, `JSM_CLIENT_ID`, `JSM_CLIENT_SECRET`, `JSM_INITIAL_REFRESH_TOKEN`).

### 1.1 Autorización de Jira Service Management (OAuth 2.0)
Para poder usar la integración con JSM (por ejemplo, buscar un usuario por su teléfono), el servicio requiere un Refresh Token inicial:
1. Asegúrate de tener tu `JSM_CLIENT_ID` y `JSM_CLIENT_SECRET` en el `.env`.
2. Corre el script interactivo para autorizar la integración por única vez: `python aux_scripts/atlassian_oauth_test.py`.
3. Esto abrirá tu navegador. Concede los permisos y vuelve a la terminal.
4. Toma el `Refresh Token` que te devolverá el script en la consola y ponlo en tu variable `JSM_INITIAL_REFRESH_TOKEN`.
El servicio se encargará a partir de ahora de reciclar el token automáticamente guardando la memoria en `data/jsm_tokens.json`.

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

### C. Webhook (WhatsApp/Twilio)

Este endpoint recibe mensajes de WhatsApp vía Twilio, consulta al agente y responde.

- **Endpoint**: `POST /api/v1/webhook`
- **Seguridad**: Valida la firma de Twilio (`X-Twilio-Signature`) usando `TWILIO_AUTH_TOKEN`.
- **Formato**: `application/x-www-form-urlencoded`.

**Prueba Local (con token configurado):**

Si tienes `TWILIO_AUTH_TOKEN` en tu `.env`, Twilio rechazará peticiones sin firma válida (esto es correcto). Para probar con `curl`, obtendrás un 403.

```bash
curl -X POST http://localhost:8000/api/v1/webhook \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "Body=Hola agente&From=+123456789"
```

_Respuesta esperada (con token activo y sin firma):_ `403 Forbidden`

_Respuesta esperada (sin token configurado o con firma válida):_ XML de Twilio con la respuesta del agente.

### D. Búsqueda de un Cliente en Jira Service Management (CSM)
Puedes usar scripts sueltos de utilería para testear por consola la conexión a la API de Jira y asegurarte de tener sincronizado tu `JSM_CLOUD_ID`:

1. **Obtener lista de Detail Fields configurados en tu tenant:**
   `python aux_scripts/list_detail_fields.py`
   Útil para verificar nombres de campos exactos (ej. _"Teléfono asociado"_ vs _"Teléfono de contacto"_).
2. **Obtener perfil de Customer a través de ese Detail Field:**
   `python aux_scripts/test_jira_customer.py`
   (Edita el valor de búsqueda dentro del archivo `.py` previo a ejecutarlo).

## 4. Solución de Problemas Comunes

- **Error 500 en Ingesta**: Verifica que `lxml` esté instalado y que las credenciales de Confluence en `.env` sean correctas (el API Token debe ser válido).
- **Error 403 Forbidden**: Verifica que el header `X-API-KEY` coincida exactamente con lo que tienes en `.env`.
- **LangChain/Pydantic Error**: Asegúrate de estar usando una versión de Python compatible (3.10 - 3.12) y no la 3.14 (experimental).
