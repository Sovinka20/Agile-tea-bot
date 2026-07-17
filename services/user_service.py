from database import get_db_connection
from utils.helpers import get_current_date
import logging

logger = logging.getLogger(__name__)

def add_user_tea_choice(user_id, username, tea_id):
    """Записывает выбор чая пользователем."""
    date = get_current_date()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (user_id, username, date, select_tea, age, gender)
                VALUES (%s, %s, %s, %s, 0, 'u')
            """, (user_id, username, date, tea_id))
            conn.commit()
