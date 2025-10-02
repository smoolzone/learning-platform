import os
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("OPENROUTER_BASE_URL")

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Initialize LLM and embeddings
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
    temperature=0.7
)
embeddings = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002"))

@router.get("/chat/{topic}")
async def chat_view(request: Request, topic: str):
    return templates.TemplateResponse("chat.html", {"request": request, "topic": topic})

@router.post("/chat/{topic}")
async def chat_query(request: Request, topic: str, query: str = Form(...)):
    try:
        persist_dir = f"knowledge_bases/{topic}/chroma_db"
        
        if not os.path.exists(persist_dir):
            return f"<div class='message ai error'>No knowledge base found for {topic}. Please check if content was ingested.</div>"
        
        vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        template = """You are a helpful AI assistant specializing in {topic}. Use the following context to answer the query. 
        Guide the user on their learning path, recommend specific content (videos, books, presentations) from our {topic} collection, 
        and focus on practical applications.

        Context: {context}

        Query: {query}

        Please provide a comprehensive answer and suggest relevant learning materials:"""

        prompt = ChatPromptTemplate.from_template(template)
        
        chain = (
            {
                "context": retriever | (lambda docs: "\n\n".join(doc.page_content for doc in docs)),
                "query": RunnablePassthrough(),
                "topic": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        
        response = chain.invoke({"query": query, "topic": topic})
        
        # Escape HTML to prevent XSS
        import html
        safe_response = html.escape(response)
        
        return f"<div class='message ai'><strong>AI:</strong> {safe_response}</div>"
    
    except Exception as e:
        return f"<div class='message ai error'>Error: {str(e)}</div>"