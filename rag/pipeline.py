import os
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from rag.vector_store import load_vector_db
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    # Setup LLM based on Env vars
    # This example uses ChatOpenAI which covers OpenAI, DeepSeek (via compatible API), etc.
    
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE") # Optional for DeepSeek/Local
    
    if not api_key or "your_" in api_key:
        print("Warning: OPENAI_API_KEY is not set correctly.")
        # Return a mock or handle gracefully? For now let it crash or warn.
    
    return ChatOpenAI(
        model="gpt-3.5-turbo", # Change to deepseek-chat if using DeepSeek
        openai_api_key=api_key,
        openai_api_base=base_url,
        temperature=0.7
    )

def answer_question(query: str):
    db = load_vector_db()
    if not db:
        return "I haven't learned anything yet! Please run the ingestion script first."
    
    retriever = db.as_retriever(search_kwargs={"k": 3})
    llm = get_llm()
    
    prompt_template = """Use the following pieces of context to answer the question at the end. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    Context: {context}
    
    Question: {question}
    Answer:"""
    
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )
    
    try:
        result = qa_chain.invoke({"query": query})
        return result["result"]
    except Exception as e:
        return f"Error processing request: {e}"
