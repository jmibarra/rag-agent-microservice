import re
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from app.services.llm_factory import LLMFactory
from app.services.vector_store import get_vector_store
from app.services.jira_service import jira_service


def _format_chat_history(history: list) -> list:
    if not history:
        return []
    messages = []
    for msg in history:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg.get("content", "")))
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg.get("content", "")))
    return messages


@tool
def create_jira_ticket(
    summary: str,
    description: str,
    producto_id: str,
    proceso_id: str = None,
    afectacion_id: str = None,
    customer_id: str = None,
) -> str:
    """
    CRITICAL: DO NOT INVENT OR GUESS PARAMETERS.
    DO NOT CALL THIS TOOL UNLESS THE USER HAS FILLED THE FORM AND EXPLICITLY CONFIRMED.

    Parameters:
    - summary: The text provided by the user for 'Resumen'.
    - description: The text provided by the user for 'Descripción'.
    - producto_id: The ID corresponding to 'Producto'.
    - proceso_id: The ID corresponding to 'Proceso afectado'.
    - afectacion_id: The ID corresponding to 'Nivel de afectación'.
    """
    # Lógica de negocio movida al tool para mantener la primitiva limpia
    payload = {
        "serviceDeskId": "2",
        "requestTypeId": "22",
        "requestFieldValues": {
            "summary": summary,
            "description": description,
            "customfield_10066": [{"id": producto_id}],
        },
    }

    if customer_id:
        payload["raiseOnBehalfOf"] = customer_id
        payload["requestParticipants"] = [customer_id]

    # Objeto 'form' con los IDs descubiertos para RT 22
    if proceso_id or afectacion_id:
        payload["form"] = {"answers": {}}
        if proceso_id:
            payload["form"]["answers"]["1"] = {"choices": [proceso_id]}
        if afectacion_id:
            payload["form"]["answers"]["2"] = {"choices": [afectacion_id]}

    print(payload)
    # Llamada directa a la primitiva
    return jira_service.create_customer_request(payload)


def generate_response(
    query: str, chat_history: list = None, customer_context: str = None
):
    # Inicializo el LLM y el vector store
    llm = LLMFactory.create_llm()
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    # Tool de busqueda en Docs
    retriever_tool = create_retriever_tool(
        retriever,
        "search_internal_docs",
        "Search internal documentation to answer user queries. Always use this first before creating a ticket unless explicitly asked to create a ticket.",
    )

    tools = [retriever_tool, create_jira_ticket]

    user_registered = customer_context is not None
    user_status_msg = (
        "IDENTIFICADO" if user_registered else "ANÓNIMO (SIN ACCESO A TICKETS)"
    )

    security_rules = ""
    if user_registered:
        security_rules = (
            "1. El usuario está IDENTIFICADO. NUNCA digas que su número no está registrado.\n"
            "2. Si la información de un ticket de Jira no es encontrada, informa que parece no estar asociado a su cuenta.\n"
            "3. Puedes dar detalles de tickets de Jira si la información está disponible."
        )
    else:
        security_rules = (
            "1. El usuario es 'ANÓNIMO'. TIENES PROHIBIDO dar detalles de tickets de Jira o crear tickets.\n"
            "2. Responde EXACTAMENTE: 'Lo siento, no tienes acceso a esa información ya que tu número no está registrado en nuestro sistema.'"
        )

    # -- DYNAMIC METADATA --
    meta = jira_service.get_incident_fields_meta()

    def format_mapping(opts):
        return (
            "\n".join([f"- {o['value']}: ID {o['id']}" for o in opts])
            if opts
            else "No disponible"
        )

    def format_labels(opts):
        return ", ".join([o["value"] for o in opts]) if opts else "No disponible"

    producto_mapping = format_mapping(meta.get("producto"))
    producto_labels = format_labels(meta.get("producto"))

    proceso_mapping = format_mapping(meta.get("proceso"))
    proceso_labels = format_labels(meta.get("proceso"))

    impacto_mapping = format_mapping(meta.get("impacto"))
    impacto_labels = format_labels(meta.get("impacto"))

    system_prompt = (
        "Eres un asistente de soporte técnico. TU PRIORIDAD ES SEGUIR EL FLUJO SIN ADIVINAR.\n"
        f"ESTADO ACTUAL DEL USUARIO: {user_status_msg}\n\n"
        "REGLA DE ORO: TIENES PROHIBIDO USAR LA HERRAMIENTA `create_jira_ticket` CON DATOS INVENTADOS O SIN CONFIRMACIÓN.\n\n"
        "MAPEO DE OPCIONES (Usa el ID correspondiente al llamar a la herramienta):\n"
        f"PRODUCTOS:\n{producto_mapping}\n"
        f"PROCESOS:\n{proceso_mapping}\n"
        f"AFECTACIÓN:\n{impacto_mapping}\n\n"
        "FLUJO DE TRABAJO OBLIGATORIO:\n"
        "1. Revisa SIEMPRE el `chat_history` para ver si el usuario ya respondió a preguntas anteriores.\n"
        "2. Intenta SIEMPRE resolver la duda usando `search_internal_docs`.\n"
        "3. Si no se resuelve o el ticket no es encontrado, PROPÓN crear un 'Incidente'.\n"
        "4. SI EL USUARIO TODAVÍA NO HA DADO LOS DATOS (revisa la historia), envía este formulario EXACTO:\n"
        "   'Para proceder con la creación del incidente, necesitaré que me proporciones la siguiente información obligatoria:\n"
        "   1. Resumen corto del problema.\n"
        "   2. Descripción detallada del evento.\n"
        f"   3. Producto afectado (Opciones: {producto_labels}).\n"
        f"   4. Proceso afectado (Opciones: {proceso_labels}).\n"
        f"   5. Nivel de afectación (Opciones: {impacto_labels}).\n"
        "   Por favor, proporciona la información solicitada para proceder.'\n"
        "5. SI DETECTAS EN EL HISTORIAL QUE EL USUARIO YA DIO LOS 5 DATOS, muestra el resumen y PREGUNTA: '¿Deseas que cree el ticket con estos datos?'.\n"
        "6. SOLO SI RESPONDE 'SÍ', llama a `create_jira_ticket` usando los IDs de opción correctos.\n\n"
        "PROHIBICIONES CRÍTICAS:\n"
        "- NO REPITAS el formulario si el usuario ya respondió los campos.\n"
        "- NO INVENTES ningún dato.\n"
        f"{security_rules}\n"
        "4. PROHIBIDO CREAR TICKETS RECURSIVOS.\n"
        "5. Responde SIEMPRE en Español."
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, tools=tools, verbose=True, return_intermediate_steps=True
    )

    formatted_history = _format_chat_history(chat_history or [])

    # -- JIRA INTEGRATION --
    jira_context = ""
    keys = re.findall(r"\b[A-Z]{2,}-\d+\b", query)
    if keys:
        jira_infos = []
        if user_registered:
            for key in keys:
                info = jira_service.get_issue_details_filtered(key, customer_context)
                if info:
                    jira_infos.append(info)
                else:
                    jira_infos.append(f"Jira Ticket {key}: Information NOT found.")
        else:
            jira_infos.append("Acceso denegado a información de tickets Jira.")

        if jira_infos:
            jira_context = "\n\n[INFO DE TICKETS RELACIONADOS]:\n" + "\n---\n".join(
                jira_infos
            )

    full_input = query + jira_context

    if user_registered:
        full_input += f"\n\n[USER CONTEXT]: {customer_context}"
    else:
        full_input += "\n\n[USER CONTEXT]: USUARIO NO REGISTRADO."

    result = agent_executor.invoke(
        {
            "input": full_input,
            "chat_history": formatted_history,
            "customer_id": customer_context.get("id") if customer_context else None,
            "customer_email": (
                customer_context.get("email") if customer_context else None
            ),
        }
    )

    context_used = []
    if "intermediate_steps" in result:
        for action, tool_output in result["intermediate_steps"]:
            if action.tool == "search_internal_docs":
                context_used.append(str(tool_output)[:200] + "...")

    return {"answer": result.get("output", ""), "context_used": context_used}
