import os
import json
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI(title="Learning Platform")

# Mount static files
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory="templates")

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "agentica-org/deepcoder-14b-preview:free"

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

async def query_openrouter(prompt: str, topic: str) -> str:
    """Query OpenRouter AI"""
    if not OPENROUTER_API_KEY:
        return "⚠️ OpenRouter API key not configured."
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Learning Platform"
        }
        
        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": f"You are an expert in {topic}. Provide helpful, accurate information."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"⚠️ API Error {response.status_code}"
                
    except Exception as e:
        return f"⚠️ Connection error: {str(e)}"

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "topics": TOPICS,
        "current_topic": "natural_health"
    })

@app.get("/browse/{topic}", response_class=HTMLResponse)
async def browse_topic(request: Request, topic: str):
    if topic not in TOPICS:
        return templates.TemplateResponse("404.html", {"request": request})
    
    topic_data = TOPICS[topic]
    return templates.TemplateResponse("browse.html", {
        "request": request,
        "topic": topic,
        "topic_data": topic_data,
        "current_topic": topic
    })

@app.get("/chat/{topic}", response_class=HTMLResponse)
async def chat_page(request: Request, topic: str):
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "topic": topic,
        "topic_data": TOPICS.get(topic, {"name": topic}),
        "current_topic": topic
    })

@app.post("/chat/{topic}/query")
async def chat_query(request: Request, topic: str, message: str = Form(...)):
    """AI response - FIXED NEWLINE ISSUE"""
    if not message.strip():
        return '<div class="message error">Please enter a message</div>'
    
    # Get AI response
    ai_response = await query_openrouter(message, topic)
    
    # FIXED: Use single line string concatenation to avoid newlines
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
        '<strong>AI Assistant</strong>'
        '</div>'
        '<div class="message-content">' + ai_response + '</div>'
        '</div>'
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)