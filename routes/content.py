from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.models.db import load_content
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/browse/{topic}")
async def browse_topic(request: Request, topic: str):
    """Browse all content types for a topic"""
    content_types = ["books", "videos", "presentations"]
    return templates.TemplateResponse("browse_topic.html", {
        "request": request, 
        "topic": topic, 
        "content_types": content_types
    })

@router.get("/browse/{topic}/{content_type}")
async def browse_content(request: Request, topic: str, content_type: str):
    content = load_content(topic, content_type)
    return templates.TemplateResponse("browse_content.html", {
        "request": request, 
        "topic": topic, 
        "content_type": content_type, 
        "content": content
    })