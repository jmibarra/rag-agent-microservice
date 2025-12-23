from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from app.services.llm_factory import LLMFactory
from app.services.vector_store import get_vector_store

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

def generate_response(query: str, chat_history: list = None):
    # Inicializo el LLM y el vector store
    llm = LLMFactory.create_llm()
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    # Preparo el historial del chat
    formatted_history = _format_chat_history(chat_history or [])

    # 1. Contextualizo la pregunta y agrego la historia al retriever
    # Esta cadena maneja la reformulación de la pregunta si hay historia
    if formatted_history:
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )
    else:
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

    # 2. Creo el prompt de respuesta a la pregunta
    system_prompt = (
        "You are an assistant for passing questions about the company's internal documentation. "
        "Use the following pieces of retrieved context to answer the question at the end. "
        "If you don't know the answer, just say that you don't know, don't try to make up an answer. "
        "IMPORTANT: You must ALWAYs answer in Spanish, regardless of the input language."
        "\n\n"
        "{context}"
    )
    
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # Creo el RAG chain
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    # -- JIRA INTEGRATION --
    import re
    from app.services.jira_service import jira_service

    # Detectar keys tipo PROJECT-123
    jira_context = ""
    # Busca patrones de 2+ mayúsculas, guión y dígitos
    keys = re.findall(r'\b[A-Z]{2,}-\d+\b', query)
    if keys:
        jira_infos = []
        for key in keys:
            info = jira_service.get_issue_details(key)
            print(f" [DEBUG JIRA] Key: {key} | Result: {info}")
            if info:
                jira_infos.append(info)
            else:
                # Explicitly inform the model that the ticket was searched but not found/allowed
                jira_infos.append(f"Jira Ticket {key}: Information NOT found. The ticket might not exist, or access is restricted (check 'JIRA_ALLOWED_PROJECTS').")
        
        if jira_infos:
            jira_context = "\n\n[INFORMACIÓN EN TIEMPO REAL / SYSTEM NOTICES]:\n" + "\n---\n".join(jira_infos)
    
    # Inyectamos el contexto de Jira en la query o como variable extra.
    # Dado que create_retrieval_chain espera 'input', podemos enriquecer el input
    # pero eso afectaría al retriever (buscaría cosas de Jira en Confluence).
    # Estrategia: Modificar el input SOLO para la generation, pero el retriever usa el input original.
    # Sin embargo, el create_retrieval_chain orquesta todo.
    # Mejor estrategia simple: Append al input. El retriever buscará sobre los tickets también (lo cual no es malo,
    # puede hallar docs relacionados) y el LLM tendrá la info explícita al final.
    
    full_input = query + jira_context

    result = rag_chain.invoke({
        "input": full_input,
        "chat_history": formatted_history
    })
    
    return {
        "answer": result["answer"],
        "context_used": [doc.page_content[:200] + "..." for doc in result["context"]]
    }
