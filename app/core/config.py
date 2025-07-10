import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()
class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC")
    DATABASE_URL: str = os.getenv("DATABASE_URL")

settings = Settings()
