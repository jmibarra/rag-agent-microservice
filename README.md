# RAG Agent Microservice

Este proyecto implementa un microservicio API RAG (Generación Aumentada por Recuperación) diseñado para actuar como backend de un agente de soporte. Utiliza LangChain para la orquestación, ChromaDB como base de datos vectorial y permite configurar LLMs como OpenAI o Google Gemini.

## Documentación

Para obtener información detallada sobre el diseño y el uso del sistema, consulta los siguientes documentos:

- **[Diseño de Solución](doc/solution_design.md)**: Explica la arquitectura, el stack tecnológico y los flujos principales (Ingesta, Chat, Webhook).
- **[Manual de Uso](doc/manual_de_uso.md)**: Guía paso a paso para configurar el entorno local, iniciar el servidor y probar los endpoints.

## Inicio Rápido

Para levantar el servicio localmente:

1.  Configura tu entorno y dependencias.
2.  Ejecuta `uvicorn app.main:app --reload`.

Consulta el [Manual de Uso](doc/manual_de_uso.md) para más detalles.
