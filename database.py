# FILE: database.py
# ROLE: Контекстный менеджер подключения к БД
# DEPENDS: config.py
# COMMANDS: (нет)
import psycopg2
from contextlib import contextmanager
from config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД."""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
    except Exception as e:
        logger.error(f"Ошибка подключения к БД: {e}")
        raise
    finally:
        if conn:
            conn.close()
