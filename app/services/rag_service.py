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
    # Initialize LLM and Vector Store
    llm = LLMFactory.create_llm()
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    # Prepare chat history
    formatted_history = _format_chat_history(chat_history or [])

    # 1. Contextualize question prompt
    # This chain handles rephrasing the question if there is history
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
        # If no history, just use the plain retriever, effectively standard RAG
        # However, for consistency in the pipeline below we can still use the wrapper
        # or just treat the 'retriever' as is. 
        # To simplify code paths, we'll just use the base retriever if no history 
        # is strictly required, but create_history_aware_retriever works fine even with empty history.
        # Let's stick to the pattern to handle future history seamlessly.
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

    # 2. Answer question prompt
    system_prompt = (
        "Use the following pieces of context to answer the question at the end. "
        "If you don't know the answer, just say that you don't know, don't try to make up an answer."
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

    # Create the RAG chain
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    # Invoke
    result = rag_chain.invoke({
        "input": query,
        "chat_history": formatted_history
    })
    
    return {
        "answer": result["answer"],
        "context_used": [doc.page_content[:200] + "..." for doc in result["context"]]
    }
