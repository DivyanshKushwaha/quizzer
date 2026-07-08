from contextlib import contextmanager
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from config import Configs

config = Configs()
_pool = None


@contextmanager
def get_connection():
    global _pool
    if _pool is None:
        _pool = pool.ThreadedConnectionPool(
            1,
            10,
            dbname=config.POSTGRES_DB,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            options=f"-c search_path=public,{config.POSTGRES_SCHEMA}",
        )
    conn = _pool.getconn()
    conn.cursor_factory = RealDictCursor
    try:
        yield conn
    finally:
        _pool.putconn(conn)
