import json
import os
from typing import List, Dict, Any

def load_content(topic: str, content_type: str) -> List[Dict[str, Any]]:
    """Load content metadata from JSON files"""
    file_path = f"content/{topic}/{content_type}/{content_type}.json"
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    
    # Fallback: scan directory for files
    content_dir = f"content/{topic}/{content_type}"
    if os.path.exists(content_dir):
        content_items = []
        for file in os.listdir(content_dir):
            if file.endswith(('.pdf', '.txt', '.md')):
                content_items.append({
                    "title": file.replace('_', ' ').title().replace('.pdf', ''),
                    "filename": file,
                    "type": content_type[:-1]  # Remove 's' (books -> book)
                })
        return content_items
    
    return []

def get_available_topics() -> List[str]:
    """Get list of available topics"""
    content_dir = "content"
    if os.path.exists(content_dir):
        return [d for d in os.listdir(content_dir) if os.path.isdir(os.path.join(content_dir, d))]
    return []