import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def setup_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bot_users (
                    user_id        BIGINT PRIMARY KEY,
                    username       TEXT,
                    first_name     TEXT,
                    started_at     TIMESTAMPTZ DEFAULT NOW(),
                    updated_at     TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS nomination_log (
                    id                   SERIAL PRIMARY KEY,
                    nominated_user_id    BIGINT NOT NULL,
                    nominated_by_user_id BIGINT NOT NULL,
                    group_chat_id        BIGINT NOT NULL,
                    created_at           TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        conn.commit()
    print("Database tables ready.")


def has_started_bot(user_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM bot_users WHERE user_id = %s", (user_id,)
            )
            return cur.fetchone() is not None


def register_user(user_id: int, username: str | None, first_name: str | None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO bot_users (user_id, username, first_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE
                    SET username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        updated_at = NOW()
            """, (user_id, username, first_name))
        conn.commit()


def log_nomination(nominated_user_id: int, nominated_by_user_id: int, group_chat_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO nomination_log (nominated_user_id, nominated_by_user_id, group_chat_id)
                VALUES (%s, %s, %s)
            """, (nominated_user_id, nominated_by_user_id, group_chat_id))
        conn.commit()


def get_user_by_username(username: str) -> dict | None:
    """Look up a user by their Telegram username (without @)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, username, first_name FROM bot_users WHERE LOWER(username) = LOWER(%s)",
                (username,)
            )
            row = cur.fetchone()
            return dict(row) if row else None


def get_nomination(nominated_user_id: int) -> dict | None:
    """
    Return the most recent nomination record for a user.
    Provides nominated_by_user_id and group_chat_id for the API payload.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT nominated_by_user_id, group_chat_id
                FROM nomination_log
                WHERE nominated_user_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (nominated_user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
