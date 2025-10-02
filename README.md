🌿 Learning Platform
A modern web-based learning platform for exploring specialized knowledge topics with AI-powered assistance. Built with FastAPI, HTMX, and OpenRouter AI.

✨ Features
🤖 AI-Powered Assistant: Real-time chat interface powered by OpenRouter AI models

📚 Topic-Based Learning: Organized content around specialized subjects

🎨 Modern Dark UI: Clean, responsive design with dark theme

⚡ HTMX Integration: Dynamic interactions without JavaScript complexity

🔍 Multiple Topics:

Natural Health 🌿

Lost History 🏛️

Apocrypha 📜

🚀 Quick Start
Prerequisites
Python 3.8+

OpenRouter API account

Modern web browser

Installation
Clone the repository

bash
git clone <repository-url>
cd learning_platform
Create virtual environment

bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies

bash
pip install fastapi uvicorn python-dotenv jinja2 httpx
Set up environment variables

bash
# Create .env file
echo "OPENROUTER_API_KEY=your_api_key_here" > .env
Get OpenRouter API Key

Visit OpenRouter

Create account and get API key

Add payment method if required

Update .env with your key

Run the application

bash
python main.py
Access the platform

text
http://localhost:8000
🏗️ Project Structure
text
learning_platform/
├── main.py                 # FastAPI application
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
├── static/
│   └── htmx.min.js       # HTMX library
└── templates/
    ├── base.html         # Base template with sidebar
    ├── index.html        # Homepage with topic grid
    ├── browse.html       # Topic content browser
    └── chat.html         # Dedicated chat interface
🎯 Usage
Browsing Content
Homepage: View all available topics

Browse: Click "Browse Content" to explore topic-specific resources

AI Integration: Use "Ask AI" buttons for contextual assistance

AI Assistant
Sidebar Chat: Always available on all pages

Topic-Specific: AI context changes based on current topic

Real-time: Instant responses using OpenRouter models

Contextual: Ask about specific content items

Supported Content Types
📹 Videos (YouTube embeds)

📚 Books & PDFs

🎯 Presentations

🔗 External resources

🔧 Configuration
Environment Variables
bash
OPENROUTER_API_KEY=your_openrouter_api_key
AI Model Configuration
Edit main.py to change the AI model:

python
MODEL = "anthropic/claude-3.5-sonnet"  # Change to any OpenRouter model
Available Models
anthropic/claude-3.5-sonnet

openai/gpt-4

google/gemini-pro

And many others

🎨 Customization
Adding New Topics
Update TOPICS dictionary in main.py

Add content to the topic structure

The AI will automatically adapt to new topics

Styling
Modify CSS in templates/base.html

Dark theme colors in CSS variables

Responsive design breakpoints

Content Management
Add videos: Update CONTENT dictionary

Add PDFs: Place in appropriate topic folder

External resources: Add URLs to content structure

🛠️ Development
Running in Development
bash
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
API Endpoints
GET / - Homepage

GET /browse/{topic} - Browse topic content

GET /chat/{topic} - Dedicated chat page

POST /chat/{topic}/query - AI chat endpoint

Technology Stack
Backend: FastAPI, Python

Frontend: Jinja2 templates, HTMX

AI: OpenRouter API

Styling: Custom CSS with dark theme

Server: Uvicorn ASGI server

🚀 Deployment
Production Deployment
Set production environment variables

Use production ASGI server

bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
Configure reverse proxy (nginx/Apache)

Set up SSL certificates

Configure domain and DNS

Docker Deployment
dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
🔒 Security Considerations
Keep API keys secure in environment variables

Implement rate limiting for API endpoints

Validate and sanitize user input

Use HTTPS in production

Regular dependency updates

🤝 Contributing
Fork the repository

Create feature branch (git checkout -b feature/amazing-feature)

Commit changes (git commit -m 'Add amazing feature')

Push to branch (git push origin feature/amazing-feature)

Open Pull Request

📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

🆘 Troubleshooting
Common Issues
AI not responding:

Check OpenRouter API key in .env

Verify account has sufficient credits

Check API rate limits

Layout issues:

Clear browser cache

Check HTMX is loading (F12 Developer Tools)

Verify static file paths

Server errors:

Check Python version compatibility

Verify all dependencies installed

Check port 8000 availability

Getting Help
Check OpenRouter documentation

Review FastAPI docs

HTMX examples

🎉 Acknowledgments
FastAPI for the excellent web framework

HTMX for modern hypermedia

OpenRouter for AI model access

Tailwind CSS for design inspiration

Happy Learning! 🌟
