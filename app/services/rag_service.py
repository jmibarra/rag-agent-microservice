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
    summary: str, description: str, producto_id: str, customer_id: str = None
) -> str:
    """
    Creates a Jira Service Management ticket.
    CRITICAL: ONLY use this tool if the user EXPLICITLY DEMANDS or CONFIRMS they want to create a ticket. Do NOT create a ticket automatically if you don't know the answer. If you don't know the answer, SUGGEST creating one and wait for their response.
    You MUST extract the 'customer_id' from the USER_CONTEXT if it was provided, and pass it here.

    'producto_id' is REQUIRED and MUST be one of the following numeric IDs based on what product the user reports:
    10026: Agilis - AMS
    10024: Agilis - Fics
    10031: Agilis - FRM
    10346: Agilis - Lean
    10025: Agilis - PXP
    10028: App - Frixo
    10027: App - Hefesto
    10029: App - Jano
    10030: App - Prometeus
    10032: B2C - Carro de compras
    10033: Reportes
    10034: Otro

    CRITICAL: If the user hasn't specified which product they are using, do NOT guess and do NOT use 'Otro' by default. Instead, ASK the user which product from the list they are having an issue with.
    """
    return jira_service.create_customer_request(
        summary, description, producto_id, customer_id
    )


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

    system_prompt = (
        "You are an assistant for answering questions about the company.\n"
        "1. Answer questions using the `search_internal_docs` tool if possible.\n"
        "2. CRITICAL RULE: NEVER create a Jira ticket automatically. ONLY use the `create_jira_ticket` tool if the user EXPLICITLY requests or confirms they want you to create one. If you cannot answer a question, simply say you don't know and suggest they can ask you to create a ticket if they want to.\n"
        "CRITICAL: If the user context says 'UNREGISTERED', you MUST REFUSE to give any information about tickets, or personal data. Just say they don't have access.\n"
        "IMPORTANT: ALWAYS answer in Spanish.\n"
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
        if customer_context:
            for key in keys:
                info = jira_service.get_issue_details(key)
                print(f" [DEBUG JIRA] Key: {key} | Result: {info}")
                if info:
                    jira_infos.append(info)
                else:
                    jira_infos.append(f"Jira Ticket {key}: Information NOT found.")
        else:
            jira_infos.append(
                "Jira Ticket: No info available. User is UNREGISTERED. Tell them they don't have access."
            )

        if jira_infos:
            jira_context = (
                "\n\n[SYSTEM NOTICE: Info about mentioned Jira tickets]:\n"
                + "\n---\n".join(jira_infos)
            )

    full_input = query + jira_context

    print(customer_context)
    if customer_context:
        full_input += (
            f"\n\n[USER CONTEXT]: The following is data about the user: {customer_context}. "
            "Extract the 'Id' field and use it as 'customer_id' if you need to create a ticket."
        )
    else:
        full_input += "\n\n[USER CONTEXT]: UNREGISTERED. You do NOT have permission to provide any information about tickets or accounts. RESPOND EXACTLY: 'Lo siento, no tienes acceso a esa información ya que tu número no está registrado en nuestro sistema.'"

    print("BEFORE ANSWER")
    print(full_input)

    result = agent_executor.invoke(
        {"input": full_input, "chat_history": formatted_history}
    )

    context_used = []
    if "intermediate_steps" in result:
        for action, tool_output in result["intermediate_steps"]:
            if action.tool == "search_internal_docs":
                context_used.append(str(tool_output)[:200] + "...")

    return {"answer": result.get("output", ""), "context_used": context_used}
