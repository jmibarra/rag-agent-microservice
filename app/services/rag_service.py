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
def create_jira_ticket(summary: str, description: str, customer_id: str = None) -> str:
    """
    Creates a Jira Service Management ticket. 
    Use this tool when the user asks to create a ticket or when you cannot answer their question with the knowledge base.
    You MUST extract the 'customer_id' from the USER_CONTEXT if it was provided, and pass it here.
    """
    return jira_service.create_customer_request(summary, description, customer_id)

def generate_response(query: str, chat_history: list = None, customer_context: str = None):
    # Inicializo el LLM y el vector store
    llm = LLMFactory.create_llm()
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    # Tool de busqueda en Docs
    retriever_tool = create_retriever_tool(
        retriever,
        "search_internal_docs",
        "Search internal documentation to answer user queries. Always use this first before creating a ticket unless explicitly asked to create a ticket."
    )

    tools = [retriever_tool, create_jira_ticket]

    system_prompt = (
        "You are an assistant for answering questions based on the company's internal documentation.\n"
        "1. First, try to answer the question using the `search_internal_docs` tool.\n"
        "2. If you cannot find the answer, or if the user EXPLICITLY asks to raise a ticket, "
        "use the `create_jira_ticket` tool.\n"
        "3. If you create a ticket, summarize what you did for the user.\n"
        "IMPORTANT: You must ALWAYS answer in Spanish, regardless of the input language.\n"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True)

    formatted_history = _format_chat_history(chat_history or [])

    # -- JIRA INTEGRATION --
    jira_context = ""
    keys = re.findall(r'\b[A-Z]{2,}-\d+\b', query)
    if keys:
        jira_infos = []
        for key in keys:
            info = jira_service.get_issue_details(key)
            print(f" [DEBUG JIRA] Key: {key} | Result: {info}")
            if info:
                jira_infos.append(info)
            else:
                jira_infos.append(f"Jira Ticket {key}: Information NOT found.")
        
        if jira_infos:
            jira_context = "\n\n[SYSTEM NOTICE: Info about mentioned Jira tickets]:\n" + "\n---\n".join(jira_infos)
    
    full_input = query + jira_context

    if customer_context:
        full_input += f"\n\n[USER CONTEXT]: The following is data about the user: {customer_context}. " \
                      "Extract the 'Id' field and use it as 'customer_id' if you need to create a ticket."

    result = agent_executor.invoke({
        "input": full_input,
        "chat_history": formatted_history
    })
    
    context_used = []
    if "intermediate_steps" in result:
        for action, tool_output in result["intermediate_steps"]:
            if action.tool == "search_internal_docs":
                context_used.append(str(tool_output)[:200] + "...")
                
    return {
        "answer": result.get("output", ""),
        "context_used": context_used
    }
