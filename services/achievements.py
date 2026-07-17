from database import get_db_connection
import logging

logger = logging.getLogger(__name__)

def grant_achievement(user_id, achievement_id):
    """Выдаёт достижение, если его ещё нет."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM user_achievements WHERE user_id=%s AND achievement_id=%s", (user_id, achievement_id))
            if cur.fetchone():
                return False
            cur.execute("""
                INSERT INTO user_achievements (user_id, achievement_id, date_achieved)
                VALUES (%s, %s, CURRENT_DATE)
            """, (user_id, achievement_id))
            conn.commit()
            return True

def check_and_grant_all(user_id, bot):
    """Проверяет условия и выдаёт достижения."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users WHERE user_id=%s", (user_id,))
            count = cur.fetchone()[0]
            if count >= 12:
                if grant_achievement(user_id, 2):
                    bot.send_message(user_id, "Поздравляем! Вы получили достижение 'Чайный лист'!")
            if count >= 20:
                if grant_achievement(user_id, 3):
                    bot.send_message(user_id, "Поздравляем! Вы получили достижение 'Чайный пакетик'!")
