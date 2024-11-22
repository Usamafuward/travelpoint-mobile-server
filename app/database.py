import psycopg
from psycopg.rows import dict_row
import logging
from app.config import settings

DSN = f"dbname={settings.DB_NAME} user={settings.DB_USER} password={settings.DB_PASSWORD} host={settings.DB_HOST} port={settings.DB_PORT}"

# Establishing connection
try:
    conn = psycopg.connect(DSN, row_factory=dict_row)
    cur = conn.cursor()
except Exception as e:
    logging.error(f"Error connecting to DB:\n{e}")
    conn, cur = None, None

