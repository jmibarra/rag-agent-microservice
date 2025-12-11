from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from app.services.llm_factory import LLMFactory
from app.services.vector_store import get_vector_store

def generate_response(query: str, chat_history: list = None):
    # Initialize LLM and Vector Store
    llm = LLMFactory.create_llm()
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    # Custom prompt
    system_prompt = (
        "Use the following pieces of context to answer the question at the end. "
        "If you don't know the answer, just say that you don't know, don't try to make up an answer."
        "\n\n"
        "{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    # Create the RAG chain using new LCEL constructors
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    # Invoke
    result = rag_chain.invoke({"input": query})
    
    return {
        "answer": result["answer"],
        "context_used": [doc.page_content[:200] + "..." for doc in result["context"]]
    }
