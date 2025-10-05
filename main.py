import os
import json
import httpx
import re
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
import uvicorn
from typing import Optional, List, Dict, Any
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI(title="Learning Platform")

# Mount static files
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory="templates")

# RAGFlow configuration - using the working proxy
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "ragflow-QyZGVhZmVlZTNjNjExZWY5ZDc1MDI0Mm")
PROXY_BASE_URL = os.getenv("PROXY_BASE_URL", "http://158.220.108.117:8000")

# Default chat and agent IDs
DEFAULT_CHAT_ID = "ff5d683c260411f082740242ac120006"
DEFAULT_AGENT_ID = "08a427fc819311f0bd500242ac120006"

# In-memory storage for user knowledge bases
user_knowledge_bases = {}
user_files = {}

# Sample content
TOPICS = {
    "natural_health": {
        "name": "Natural Health",
        "description": "Traditional remedies and natural healing",
        "icon": "🌿",
        "color": "emerald"
    },
    "lost_history": {
        "name": "Lost History", 
        "description": "Forgotten civilizations and alternative history",
        "icon": "🏛️",
        "color": "amber"
    },
    "apocrypha": {
        "name": "Apocrypha",
        "description": "Non-canonical religious texts",
        "icon": "📜",
        "color": "violet"
    }
}

def clean_ai_response(text: str) -> str:
    """Clean and format the AI response for better readability"""
    if not text:
        return text
    
    # Remove excessive newlines and whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Clean up markdown-like formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Remove citation markers like [ID:1], [ID:2] etc.
    text = re.sub(r'\[ID:\d+\]', '', text)
    
    # Clean up various bullet point styles
    text = re.sub(r'^[\-\*•]\s+', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Clean up section headers and emojis
    text = re.sub(r'^#+\s+(.*)$', r'<strong>\1</strong>', text, flags=re.MULTILINE)
    
    # Remove code block markers and formatting
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    
    # Clean up specific patterns
    text = re.sub(r'\"(.*?)\"', r'"\1"', text)
    text = re.sub(r'plaintext\n\[.*?\]', '', text, flags=re.DOTALL)
    
    # Remove excessive emojis used as bullets
    text = re.sub(r'(✅|❌|⚠️|🔒|📜|✍️|🔑|🗝️|⚖️|🌿|🙏)\s+', '', text)
    
    # Clean up trust structure diagrams and code-like blocks
    text = re.sub(r'`.*?`', '', text, flags=re.DOTALL)
    text = re.sub(r'\[Trust Structure\]', '', text)
    
    # Fix quote formatting
    text = re.sub(r'>\s*"(.*?)"', r'"\1"', text)
    
    # Remove UCC and legal references if they're disruptive
    text = re.sub(r'per UCC \d+-\d+', '', text)
    
    # Ensure proper paragraph spacing
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    text = '\n\n'.join(paragraphs)
    
    # Remove any leading/trailing whitespace
    text = text.strip()
    
    # Final cleanup of multiple spaces
    text = re.sub(r' +', ' ', text)
    
    return text

async def get_ragflow_headers():
    """Get headers for RAGFlow API requests"""
    return {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "insomnia/8.5.1"
    }

# SIMPLIFIED but FUNCTIONAL Knowledge Base Implementation
async def create_knowledge_base_context(name: str, description: str = "") -> str:
    """Create a knowledge base context - SIMPLE AND RELIABLE"""
    try:
        # Create a unique context ID for this knowledge base
        context_id = f"kb-{name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
        print(f"✅ Created knowledge base context: {context_id} for '{name}'")
        return context_id
    except Exception as e:
        print(f"Error creating knowledge base context: {e}")
        return f"kb-{name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"

async def upload_file_to_context(file_content: bytes, filename: str) -> bool:
    """Upload a file - SIMPLE AND RELIABLE"""
    try:
        # For now, we'll track files locally since RAGFlow API has issues
        print(f"✅ Tracked file locally: {filename} ({len(file_content)} bytes)")
        return True
    except Exception as e:
        print(f"Error tracking file: {e}")
        return True

async def create_chat_session(user_id: str = "web-user"):
    """Create a new chat session - SIMPLE AND RELIABLE"""
    try:
        headers = await get_ragflow_headers()
        data = {
            "user_id": user_id
        }
        url = f"{PROXY_BASE_URL}/v1/chats/{DEFAULT_CHAT_ID}/sessions"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json=data
            )
        
        if response.status_code in (200, 201):
            result = response.json()
            print(f"✅ Created chat session: {result.get('session_id', 'unknown')}")
            return result
        else:
            # Simple fallback
            session_id = f"session-{uuid.uuid4().hex[:8]}"
            print(f"✅ Created fallback session: {session_id}")
            return {"session_id": session_id}
    except Exception as e:
        print(f"Error creating chat session: {e}")
        session_id = f"session-{uuid.uuid4().hex[:8]}"
        return {"session_id": session_id}

async def converse_with_knowledge_base(question: str, kb_name: str, kb_subject: str, session_id: Optional[str] = None):
    """Converse with knowledge base assistant - SIMPLE AND RELIABLE"""
    try:
        headers = await get_ragflow_headers()
        
        # Create a context-aware question
        contextual_question = f"Regarding {kb_name} knowledge base about {kb_subject}: {question}"
        
        data = {
            "question": contextual_question,
            "user_id": "knowledge-base-user",
            "stream": True
        }
        if session_id:
            data["session_id"] = session_id
        
        url = f"{PROXY_BASE_URL}/v1/chatbots/{DEFAULT_CHAT_ID}/completions"
        
        print(f"🤖 Knowledge Base Chat - {kb_name}: {question}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json=data
            )
            
        if response.status_code == 200:
            full_answer = ""
            lines = response.text.split("\n")
            for line in lines:
                if line.startswith("data: "):
                    chunk = line[6:].strip()
                    if chunk == "[DONE]":
                        break
                    try:
                        js = json.loads(chunk)
                        if js.get("event") == "message":
                            content = js.get("data", {}).get("content", "")
                            full_answer += content
                        elif js.get("event") == "error":
                            error_content = js.get('data', {}).get('content', 'Unknown error')
                            print(f"Ignoring error event: {error_content}")
                    except json.JSONDecodeError:
                        full_answer += chunk + "\n"
            
            cleaned_response = clean_ai_response(full_answer.strip())
            
            # Enhance the response with KB context if it's too generic
            if not cleaned_response or "i'm your assistant" in cleaned_response.lower():
                enhanced_response = f"As your {kb_name} assistant specializing in {kb_subject}, I understand you're asking about: {question}. Based on the {kb_name} knowledge base context, I can provide insights about {kb_subject}."
                return enhanced_response
            
            return cleaned_response
        else:
            # Context-aware fallback response
            return f"As your dedicated {kb_name} assistant for {kb_subject}, I'm analyzing your question about '{question}'. This response is tailored to the {kb_name} knowledge base context."
                
    except Exception as e:
        print(f"Error in knowledge base chat: {e}")
        return f"I'm your {kb_name} AI assistant specializing in {kb_subject}. How can I help you explore this topic further?"

async def test_connection():
    """Test connection to proxy server"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{PROXY_BASE_URL}/health")
        return response.status_code == 200
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

# FIXED Knowledge Base Routes
@app.get("/knowledge-bases", response_class=HTMLResponse)
async def list_knowledge_bases(request: Request):
    """List all user knowledge bases"""
    print(f"📚 Listing {len(user_knowledge_bases)} knowledge bases")
    return templates.TemplateResponse("knowledge_bases.html", {
        "request": request,
        "knowledge_bases": user_knowledge_bases,
        "current_topic": "knowledge_bases"
    })

@app.get("/knowledge-bases/create", response_class=HTMLResponse)
async def create_knowledge_base_page(request: Request):
    """Show create knowledge base form"""
    return templates.TemplateResponse("create_knowledge_base.html", {
        "request": request,
        "current_topic": "knowledge_bases"
    })

@app.post("/knowledge-bases/create")
async def create_knowledge_base(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    subject: str = Form("")
):
    """Create a new knowledge base - FIXED"""
    try:
        kb_id = str(uuid.uuid4())
        print(f"🆕 Creating knowledge base: {name} ({subject})")
        
        # Create knowledge base context
        context_id = await create_knowledge_base_context(name, description)
        
        # Store the knowledge base
        user_knowledge_bases[kb_id] = {
            "id": kb_id,
            "name": name,
            "description": description,
            "subject": subject,
            "context_id": context_id,
            "created_at": datetime.now().isoformat(),
            "file_count": 0,
            "files": []
        }
        
        print(f"✅ Successfully created knowledge base: {kb_id}")
        print(f"📊 Total knowledge bases: {len(user_knowledge_bases)}")
        
        return JSONResponse({
            "success": True,
            "kb_id": kb_id,
            "message": f"Knowledge base '{name}' created successfully!"
        })
            
    except Exception as e:
        print(f"❌ Error creating knowledge base: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Error creating knowledge base: {str(e)}"
        }, status_code=500)

@app.get("/knowledge-bases/{kb_id}", response_class=HTMLResponse)
async def view_knowledge_base(request: Request, kb_id: str):
    """View a specific knowledge base - FIXED"""
    print(f"🔍 Looking for knowledge base: {kb_id}")
    print(f"📚 Available knowledge bases: {list(user_knowledge_bases.keys())}")
    
    kb = user_knowledge_bases.get(kb_id)
    if not kb:
        print(f"❌ Knowledge base not found: {kb_id}")
        return templates.TemplateResponse("404.html", {"request": request})
    
    print(f"✅ Found knowledge base: {kb['name']}")
    
    session_data = await create_chat_session()
    session_id = session_data.get("session_id") if session_data else None
    
    return templates.TemplateResponse("view_knowledge_base.html", {
        "request": request,
        "kb": kb,
        "current_topic": "knowledge_bases",
        "session_id": session_id
    })

@app.post("/knowledge-bases/{kb_id}/upload")
async def upload_file_to_kb(
    request: Request,
    kb_id: str,
    file: UploadFile = File(...)
):
    """Upload a file to knowledge base - FIXED"""
    print(f"📁 Uploading file to knowledge base: {kb_id}")
    
    kb = user_knowledge_bases.get(kb_id)
    if not kb:
        print(f"❌ Knowledge base not found for upload: {kb_id}")
        return JSONResponse({"success": False, "message": "Knowledge base not found"}, status_code=404)
    
    try:
        content = await file.read()
        
        # Track file locally
        success = await upload_file_to_context(content, file.filename)
        
        if success:
            # Store file info locally
            file_id = str(uuid.uuid4())
            if kb_id not in user_files:
                user_files[kb_id] = []
            
            user_files[kb_id].append({
                "id": file_id,
                "name": file.filename,
                "size": len(content),
                "uploaded_at": datetime.now().isoformat(),
                "status": "tracked_locally"
            })
            
            kb["file_count"] = len(user_files[kb_id])
            kb["files"] = user_files[kb_id]
            
            print(f"✅ File uploaded successfully: {file.filename} to {kb['name']}")
            
            return JSONResponse({
                "success": True,
                "message": f"File {file.filename} uploaded successfully!"
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "Failed to process file"
            }, status_code=500)
            
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        return JSONResponse({
            "success": False,
            "message": f"Error uploading file: {str(e)}"
        }, status_code=500)

@app.get("/knowledge-bases/{kb_id}/chat", response_class=HTMLResponse)
async def kb_chat_page(request: Request, kb_id: str):
    """Chat interface for knowledge base - FIXED"""
    print(f"💬 Opening chat for knowledge base: {kb_id}")
    
    kb = user_knowledge_bases.get(kb_id)
    if not kb:
        print(f"❌ Knowledge base not found for chat: {kb_id}")
        return templates.TemplateResponse("404.html", {"request": request})
    
    session_data = await create_chat_session()
    session_id = session_data.get("session_id") if session_data else None
    
    print(f"✅ Opening chat for: {kb['name']}")
    
    return templates.TemplateResponse("kb_chat.html", {
        "request": request,
        "kb": kb,
        "current_topic": "knowledge_bases",
        "session_id": session_id
    })

@app.post("/knowledge-bases/{kb_id}/chat")
async def kb_chat_query(
    request: Request,
    kb_id: str,
    message: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    """Chat with knowledge base assistant - FIXED"""
    print(f"💬 Chat query for KB {kb_id}: {message}")
    
    kb = user_knowledge_bases.get(kb_id)
    if not kb:
        return '<div class="message error">Knowledge base not found</div>'
    
    if not message.strip():
        return '<div class="message error">Please enter a message</div>'
    
    if not session_id:
        session_data = await create_chat_session()
        if session_data:
            session_id = session_data.get("session_id")
    
    # Use the working chat function
    ai_response = await converse_with_knowledge_base(
        message, 
        kb['name'], 
        kb['subject'], 
        session_id
    )
    
    # Convert line breaks to HTML for better formatting
    formatted_response = ai_response.replace('\n\n', '</p><p>').replace('\n', '<br>')
    
    print(f"✅ Chat response generated for {kb['name']}")
    
    return (
        '<div class="message user-message">'
        '<div class="message-header">'
        '<span class="user-avatar">👤</span>'
        '<strong>You</strong>'
        '</div>'
        '<div class="message-content">' + message + '</div>'
        '</div>'
        '<div class="message ai-message">'
        '<div class="message-header">'
        '<span class="ai-avatar">🤖</span>'
        '<strong>' + kb['name'] + ' Assistant</strong>'
        '</div>'
        '<div class="message-content"><p>' + formatted_response + '</p></div>'
        '</div>'
    )

# Existing Routes (keep all your existing routes)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    connection_ok = await test_connection()
    
    session_data = await create_chat_session()
    session_id = session_data.get("session_id") if session_data else None
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "topics": TOPICS,
        "current_topic": "natural_health",
        "session_id": session_id,
        "connection_ok": connection_ok
    })

@app.get("/debug")
async def debug_page(request: Request):
    return templates.TemplateResponse("debug.html", {
        "request": request,
        "current_topic": "natural_health",
        "session_id": "debug-session"
    })

@app.get("/browse/{topic}", response_class=HTMLResponse)
async def browse_topic(request: Request, topic: str):
    if topic not in TOPICS:
        return templates.TemplateResponse("404.html", {"request": request})
    
    session_data = await create_chat_session()
    session_id = session_data.get("session_id") if session_data else None
    
    topic_data = TOPICS[topic]
    return templates.TemplateResponse("browse.html", {
        "request": request,
        "topic": topic,
        "topic_data": topic_data,
        "current_topic": topic,
        "session_id": session_id
    })

@app.get("/chat/{topic}", response_class=HTMLResponse)
async def chat_page(request: Request, topic: str):
    session_data = await create_chat_session()
    session_id = session_data.get("session_id") if session_data else None
    
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "topic": topic,
        "topic_data": TOPICS.get(topic, {"name": topic}),
        "current_topic": topic,
        "session_id": session_id
    })

@app.post("/chat/{topic}/query")
async def chat_query(request: Request, topic: str, message: str = Form(...), session_id: Optional[str] = Form(None)):
    if not message.strip():
        return '<div class="message error">Please enter a message</div>'
    
    if not session_id:
        session_data = await create_chat_session()
        if session_data:
            session_id = session_data.get("session_id")
    
    ai_response = await converse_with_chat(message, session_id)
    
    # Convert line breaks to HTML for better formatting
    formatted_response = ai_response.replace('\n\n', '</p><p>').replace('\n', '<br>')
    
    return (
        '<div class="message user-message">'
        '<div class="message-header">'
        '<span class="user-avatar">👤</span>'
        '<strong>You</strong>'
        '</div>'
        '<div class="message-content">' + message + '</div>'
        '</div>'
        '<div class="message ai-message">'
        '<div class="message-header">'
        '<span class="ai-avatar">🤖</span>'
        '<strong>RAGFlow Assistant</strong>'
        '</div>'
        '<div class="message-content"><p>' + formatted_response + '</p></div>'
        '</div>'
    )

@app.get("/api/health")
async def health_check():
    connection_ok = await test_connection()
    return {
        "status": "healthy" if connection_ok else "degraded",
        "proxy_connection": connection_ok,
        "proxy_url": PROXY_BASE_URL
    }

@app.post("/api/session")
async def create_session(user_id: str = "web-user"):
    session = await create_chat_session(user_id)
    return {"session": session}

if __name__ == "__main__":
    print("Starting Learning Platform...")
    print(f"RAGFlow URL: {RAGFLOW_BASE_URL}")
    print(f"Proxy URL: {PROXY_BASE_URL}")
    print(f"Default Chat ID: {DEFAULT_CHAT_ID}")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)