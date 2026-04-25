import re
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from app.services.llm_factory import LLMFactory
from app.services.vector_store import get_vector_store
from app.services.jira_service import jira_service
from app.services.prompt_loader import load_prompt, render_prompt


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
    Crea un ticket de incidente en Jira Service Management.
    La descripción completa para el LLM se carga desde tool_create_ticket.md.
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

# Se sobreescribe la descripción del tool con el contenido del template externo
# para que el LLM reciba las instrucciones detalladas al invocar la herramienta
create_jira_ticket.description = load_prompt("tool_create_ticket.md")

def generate_response(
    query: str, chat_history: list = None, customer_context: str = None
):
    # Inicializo el LLM y el vector store
    llm = LLMFactory.create_llm()
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    # Tool de búsqueda en Docs (descripción cargada desde template externo)
    retriever_tool = create_retriever_tool(
        retriever,
        "search_internal_docs",
        load_prompt("tool_search_docs.md"),
    )

    tools = [retriever_tool, create_jira_ticket]

    user_registered = customer_context is not None
    user_status_msg = (
        "IDENTIFICADO" if user_registered else "ANÓNIMO (SIN ACCESO A TICKETS)"
    )

    # Reglas de seguridad cargadas desde templates externos según tipo de usuario
    security_file = "security_registered.md" if user_registered else "security_anonymous.md"
    security_rules = load_prompt(security_file)

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

    # System prompt renderizado desde template externo con variables dinámicas
    system_prompt = render_prompt(
        "system_prompt.md",
        user_status=user_status_msg,
        producto_mapping=producto_mapping,
        proceso_mapping=proceso_mapping,
        impacto_mapping=impacto_mapping,
        producto_labels=producto_labels,
        proceso_labels=proceso_labels,
        impacto_labels=impacto_labels,
        security_rules=security_rules,
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
