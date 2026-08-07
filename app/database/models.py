import logging
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from app.config import Config

logger = logging.getLogger(__name__)

# Global connection pool for Neon PostgreSQL
db_pool = None


def get_db_pool():
    global db_pool
    if db_pool is None or db_pool.closed:
        try:
            db_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=Config.NEON_DATABASE_URL
            )
            logger.info("Initialized Neon PostgreSQL ThreadedConnectionPool.")
        except Exception as e:
            logger.error(f"Failed to create Neon PostgreSQL connection pool: {e}")
            raise e
    return db_pool


def get_db_connection():
    """Get a warm connection from the connection pool."""
    try:
        p = get_db_pool()
        conn = p.getconn()
        return conn
    except Exception as e:
        logger.warning(f"Connection pool fallback to direct connection: {e}")
        return psycopg2.connect(Config.NEON_DATABASE_URL)


def release_db_connection(conn):
    """Return connection back to pool."""
    if conn is None:
        return
    try:
        p = get_db_pool()
        p.putconn(conn)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


def init_db():
    """Auto-create table 'users' and required schemas on startup."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    firebase_uid VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            logger.info("Neon Database table 'users' initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing Neon database schema: {e}")
        if conn:
            conn.rollback()
    finally:
        release_db_connection(conn)


def get_or_create_user(firebase_uid: str, email: str, name: str = None):
    """
    Look up user by firebase_uid. If found, return existing user.
    Else, insert new user into Neon DB and return created user dict.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Check if user exists
            cur.execute("SELECT * FROM users WHERE firebase_uid = %s", (firebase_uid,))
            user = cur.fetchone()
            if user:
                if name and user.get("name") != name:
                    cur.execute(
                        "UPDATE users SET name = %s, email = %s WHERE firebase_uid = %s RETURNING *",
                        (name, email, firebase_uid),
                    )
                    conn.commit()
                    user = cur.fetchone()
                return dict(user)

            # 2. Insert new user
            display_name = name or (email.split("@")[0] if email else "User")
            cur.execute(
                """
                INSERT INTO users (firebase_uid, email, name)
                VALUES (%s, %s, %s)
                RETURNING *
                """,
                (firebase_uid, email, display_name),
            )
            conn.commit()
            new_user = cur.fetchone()
            logger.info(f"Created new user in Neon DB: {email} ({firebase_uid})")
            return dict(new_user)
    except Exception as e:
        logger.error(f"Error in get_or_create_user for {firebase_uid}: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        release_db_connection(conn)


def get_user_by_firebase_uid(firebase_uid: str):
    """Fetch user dict from Neon DB by firebase_uid."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE firebase_uid = %s", (firebase_uid,))
            user = cur.fetchone()
            return dict(user) if user else None
    except Exception as e:
        logger.error(f"Error fetching user by firebase_uid {firebase_uid}: {e}")
        return None
    finally:
        release_db_connection(conn)
