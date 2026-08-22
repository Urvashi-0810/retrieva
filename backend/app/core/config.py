from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"

settings = Settings()
