# RAG Agent Microservice `v1.0.0` 🤖🚀

Este microservicio es el núcleo de inteligencia para un agente de soporte automatizado. Utiliza una arquitectura **RAG (Retrieval-Augmented Generation)** para proporcionar respuestas precisas basadas en conocimiento interno, integrado directamente con el ecosistema de Atlassian y canales de mensajería.

---

## ✨ Características Principales

- **RAG Multi-Fuente**: Ingesta y recuperación de conocimiento desde espacios de **Confluence**.
- **Agente Inteligente**: Capacidad de razonamiento y uso de herramientas (*Tool Calling*) vía **LangChain**.
- **Integración con Jira**:
    -Búsqueda de estado de tickets en tiempo real.
    -Creación automática de incidentes en **Jira Service Management**.
- **Identificación de Clientes**: Reconocimiento automático de usuarios vía **WhatsApp/Twilio** mediante el perfil de cliente en JSM.
- **Multi-LLM**: Soporte nativo para **OpenAI (GPT)** y **Google Gemini**.
- **Seguridad**: Validación de firmas de Twilio y protección de endpoints mediante API Key.

---

## 🛠️ Stack Tecnológico

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Alto rendimiento, Async)
- **Orquestador**: [LangChain](https://www.langchain.com/)
- **Base de Datos Vectorial**: [ChromaDB](https://www.trychroma.com/)
- **Modelos**: OpenAI & Google Generative AI
- **Integraciones**: Atlassian REST APIs (Jira & Confluence), Twilio SDK

---

## 📂 Estructura de Documentación

Para profundizar en el sistema, consulta los siguientes documentos detallados:

1. 📖 **[Manual de Uso](doc/manual_de_uso.md)**: Guía paso a paso para instalación, configuración de variables de entorno (`.env`) y pruebas de endpoints.
2. 🏗️ **[Diseño de Solución](doc/solution_design.md)**: Detalles sobre la arquitectura, flujos de datos y decisiones técnicas.

---

## 🚀 Inicio Rápido

1. **Clonar y Configurar**:

   ```bash
   git clone <repo-url>
   cd rag-agent-microservice
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Variables de Entorno**:
   Copia el archivo `.env.example` a `.env` y completa tus credenciales.

3. **Ejecutar**:

   ```bash
   uvicorn app.main:app --reload
   ```

El servicio estará disponible en `http://localhost:8000` y la documentación interactiva en `/docs`.

---
