import os
import json
import httpx
import re
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn
from typing import Optional

# Load environment variables
load_dotenv()

app = FastAPI(title="Learning Platform")

# Mount static files
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory="templates")

# RAGFlow configuration - using the proxy server
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "ragflow-QyZGVhZmVlZTNjNjExZWY5ZDc1MDI0Mm")
PROXY_BASE_URL = os.getenv("PROXY_BASE_URL", "http://158.220.108.117:8000")

# Default chat and agent IDs
DEFAULT_CHAT_ID = "ff5d683c260411f082740242ac120006"
DEFAULT_AGENT_ID = "08a427fc819311f0bd500242ac120006"

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
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Replace multiple newlines with double newlines
    text = re.sub(r'[ \t]+', ' ', text)  # Replace multiple spaces/tabs with single space
    
    # Clean up markdown-like formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)  # Convert **bold** to <strong>
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)  # Convert *italic* to <em>
    
    # Remove citation markers like [ID:1], [ID:2] etc.
    text = re.sub(r'\[ID:\d+\]', '', text)
    
    # Clean up various bullet point styles
    text = re.sub(r'^[\-\*•]\s+', '• ', text, flags=re.MULTILINE)  # Standardize bullet points
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)  # Remove numbered lists
    text = re.sub(r'^[❶❷❸❹❺❻❼❽❾❿]\s+', '• ', text, flags=re.MULTILINE)  # Convert numbered circles to bullets
    text = re.sub(r'^[➊➋➌➍➎➏➐➑➒➓]\s+', '• ', text, flags=re.MULTILINE)  # Convert circled numbers to bullets
    text = re.sub(r'^[➀➁➂➃➄➅➆➆➇➈➉]\s+', '• ', text, flags=re.MULTILINE)  # Convert other circled numbers
    
    # Clean up section headers and emojis
    text = re.sub(r'^#+\s+(.*)$', r'<strong>\1</strong>', text, flags=re.MULTILINE)
    
    # Remove code block markers and formatting
    text = re.sub(r'`(.*?)`', r'\1', text)  # Remove code backticks
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Remove markdown links
    
    # Clean up specific patterns from your example
    text = re.sub(r'\"(.*?)\"', r'"\1"', text)  # Normalize quotes
    text = re.sub(r'plaintext\n\[.*?\]', '', text, flags=re.DOTALL)  # Remove code blocks like "plaintext[Trust Structure]"
    
    # Remove excessive emojis used as bullets (keep only one)
    text = re.sub(r'(✅|❌|⚠️|🔒|📜|✍️|🔑|🗝️|⚖️|🌿|🙏)\s+', '', text)  # Remove emoji bullets
    
    # Clean up trust structure diagrams and code-like blocks
    text = re.sub(r'`.*?`', '', text, flags=re.DOTALL)  # Remove any remaining code blocks
    text = re.sub(r'\[Trust Structure\]', '', text)  # Remove specific markers
    
    # Fix quote formatting
    text = re.sub(r'>\s*"(.*?)"', r'"\1"', text)  # Clean up blockquote-style quotes
    
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

async def create_chat_session(user_id: str = "web-user"):
    """Create a new chat session using proxy endpoint"""
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
        print(f"Session creation URL: {url}")
        print(f"Session creation response: {response.status_code} - {response.text}")
        if response.status_code in (200, 201):
            result = response.json()
            if result.get("code") == 0 or "data" in result:
                return result
            else:
                print(f"Session creation failed: {result.get('message')}")
                return None
        else:
            print(f"Session creation error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error creating chat session: {e}")
        return None

async def converse_with_chat(question: str, session_id: Optional[str] = None, user_id: str = "web-user"):
    """Converse with chat assistant using proxy endpoint"""
    try:
        headers = await get_ragflow_headers()
        
        data = {
            "question": question,
            "user_id": user_id,
            "stream": True
        }
        if session_id:
            data["session_id"] = session_id
        
        url = f"{PROXY_BASE_URL}/v1/chatbots/{DEFAULT_CHAT_ID}/completions"
        print(f"Sending request to: {url}")
        print(f"Request data: {data}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json=data
            )
            
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
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
                            print(f"Ignoring error event: {js.get('data', {}).get('content')}")
                    except json.JSONDecodeError:
                        full_answer += chunk + "\n"
            
            # CLEAN THE RESPONSE BEFORE RETURNING
            cleaned_response = clean_ai_response(full_answer.strip())
            return cleaned_response or "No response received."
        else:
            error_msg = f"API Error {response.status_code}: {response.text}"
            print(f"Chat error: {error_msg}")
            return f"Assistant is currently unavailable. Please try again later. (Error: {response.status_code})"
                
    except Exception as e:
        print(f"Error conversing with chat: {e}")
        return f"An unexpected error occurred: {str(e)}"

async def test_proxy_endpoints():
    """Test different proxy endpoints to find the working one"""
    headers = await get_ragflow_headers()
    test_data = {
        "question": "Hello, are you working?",
        "user_id": "test-user",
        "stream": True
    }
    
    endpoints_to_test = [
        f"{PROXY_BASE_URL}/v1/chatbots/{DEFAULT_CHAT_ID}/completions",
        f"{PROXY_BASE_URL}/v1/chats/{DEFAULT_CHAT_ID}/completions",
        f"{PROXY_BASE_URL}/api/v1/chatbots/{DEFAULT_CHAT_ID}/completions",
    ]
    
    for endpoint in endpoints_to_test:
        try:
            print(f"Testing endpoint: {endpoint}")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(endpoint, headers=headers, json=test_data)
            print(f"Endpoint {endpoint}: Status {response.status_code}")
            if response.status_code == 200:
                print(f"Success with endpoint: {endpoint}")
                return endpoint
        except Exception as e:
            print(f"Endpoint {endpoint} failed: {e}")
    
    return None

async def test_connection():
    """Test connection to proxy server"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{PROXY_BASE_URL}/health")
        print(f"Health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    connection_ok = await test_connection()
    print(f"Connection test: {connection_ok}")
    
    working_endpoint = await test_proxy_endpoints()
    print(f"Working endpoint: {working_endpoint}")
    
    session_data = await create_chat_session()
    session_id = session_data.get("data", {}).get("id") if session_data else None
    
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
    session_id = session_data.get("data", {}).get("id") if session_data else None
    
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
    session_id = session_data.get("data", {}).get("id") if session_data else None
    
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
            session_id = session_data.get("data", {}).get("id")
    
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
    working_endpoint = await test_proxy_endpoints()
    return {
        "status": "healthy" if connection_ok else "degraded",
        "proxy_connection": connection_ok,
        "working_endpoint": working_endpoint,
        "proxy_url": PROXY_BASE_URL
    }

@app.post("/api/session")
async def create_session(user_id: str = "web-user"):
    session = await create_chat_session(user_id)
    return {"session": session}

# Simple fallback for testing
@app.post("/chat/{topic}/test")
async def chat_test(request: Request, topic: str, message: str = Form(...)):
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
        '<strong>Test Assistant</strong>'
        '</div>'
        '<div class="message-content">This is a test response for: ' + message + '</div>'
        '</div>'
    )

if __name__ == "__main__":
    print("Starting Learning Platform...")
    print(f"Proxy URL: {PROXY_BASE_URL}")
    print(f"Default Chat ID: {DEFAULT_CHAT_ID}")
    print("Testing endpoints...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)