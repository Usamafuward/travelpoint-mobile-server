import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DB_NAME = os.getenv("DB_NAME", "travelpoint")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "tp/3@UCSC")
    DB_HOST = os.getenv("DB_HOST", "travelpoint-db.postgres.database.azure.com")
    DB_PORT = os.getenv("DB_PORT", "5432")
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    DSN = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"

settings = Settings()
