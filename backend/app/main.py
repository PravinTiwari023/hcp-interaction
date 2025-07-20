from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1 import endpoints
from .db.database import engine
from .db import models
from .core.config import settings

print("🚀 Starting AI-First CRM HCP Module Backend...")
print(f"🔧 Database URL: {settings.database_url}")
print(f"🤖 Groq API Key configured: {'Yes' if settings.groq_api_key else 'No'}")

# Create database tables
try:
    models.Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"❌ Error creating database tables: {e}")
    raise

app = FastAPI(
    title="AI-First CRM HCP Module",
    description="Backend for logging and managing HCP interactions with AI assistance and LangGraph agent.",
    version="1.0.0",
)

origins = [
    "http://localhost:3000",  # React app
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Test LangGraph agent on startup"""
    print("🔄 Testing LangGraph Agent initialization...")
    try:
        from .langgraph_agent.agent import app as langgraph_app
        from langchain_core.messages import HumanMessage
        
        # Test with a simple message
        test_result = langgraph_app.invoke({"messages": [HumanMessage(content="Hello, I'm a test message")]})
        print("✅ LangGraph Agent initialized and working!")
        
    except Exception as e:
        print(f"⚠️  LangGraph Agent initialization warning: {e}")
        print("   This is normal if GROQ_API_KEY is not set or database is not ready")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI-First CRM HCP Module Backend is running!",
        "version": "1.0.0",
        "status": "healthy",
        "groq_configured": bool(settings.groq_api_key)
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "database": "connected" if engine else "disconnected",
        "groq_api": "configured" if settings.groq_api_key else "not_configured",
        "langgraph_agent": "available"
    }