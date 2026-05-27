from pydantic import BaseModel 
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "GAIA Python Core")
    app_source: str = os.getenv("APP_SOURCE", "python-core")
    timezone: str = os.getenv("TIMEZONE", "America/Sao_Paulo")
    environment: str = os.getenv("ENVIRONMENT", "development")
    exchange_api_key: str | None = os.getenv("EXCHANGE_API_KEY")
    exchange_api_base_url: str = os.getenv("EXCHANGE_API_BASE_URL", "https://v6.exchangerate-api.com/v6")

settings = Settings()