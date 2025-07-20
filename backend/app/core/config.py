import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:Passwords@localhost:5432/aihcp")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")

    class Config:
        env_file = ".env"

settings = Settings()

# Validate that required environment variables are set
if not settings.groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is required but not set")

print(f"✅ Environment loaded - Database: {settings.database_url}")
print(f"✅ GROQ API Key configured: {'Yes' if settings.groq_api_key else 'No'}")
