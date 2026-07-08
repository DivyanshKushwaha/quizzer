from core.database.postgres.postgres_config import get_connection


def init_tables():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.users (
                    id UUID PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'player')),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.refresh_tokens (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
                    token_hash TEXT NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    revoked BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            cur.execute("CREATE SCHEMA IF NOT EXISTS app_data;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_data.quizzes (
                    id SERIAL PRIMARY KEY,
                    admin_id VARCHAR(36) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    questions JSONB NOT NULL DEFAULT '[]',
                    settings JSONB NOT NULL DEFAULT '{}',
                    prize JSONB NOT NULL DEFAULT '{}',
                    status VARCHAR(20) NOT NULL DEFAULT 'draft',
                    started_at TIMESTAMPTZ,
                    ends_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_data.registrations (
                    id SERIAL PRIMARY KEY,
                    quiz_id INT NOT NULL REFERENCES app_data.quizzes(id) ON DELETE CASCADE,
                    player_id VARCHAR(36) NOT NULL,
                    display_name VARCHAR(100) NOT NULL,
                    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(quiz_id, player_id)
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_data.attempts (
                    id SERIAL PRIMARY KEY,
                    quiz_id INT NOT NULL REFERENCES app_data.quizzes(id) ON DELETE CASCADE,
                    player_id VARCHAR(36) NOT NULL,
                    score INT NOT NULL DEFAULT 0,
                    total_time_ms BIGINT NOT NULL DEFAULT 0,
                    question_index INT NOT NULL DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'playing',
                    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    finished_at TIMESTAMPTZ,
                    UNIQUE(quiz_id, player_id)
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_data.answers (
                    id SERIAL PRIMARY KEY,
                    attempt_id INT NOT NULL REFERENCES app_data.attempts(id) ON DELETE CASCADE,
                    question_index INT NOT NULL,
                    selected_index INT NOT NULL,
                    is_correct BOOLEAN NOT NULL,
                    time_ms INT NOT NULL,
                    answered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(attempt_id, question_index)
                );
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_quizzes_status ON app_data.quizzes(status);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_attempts_quiz ON app_data.attempts(quiz_id);")
        conn.commit()
