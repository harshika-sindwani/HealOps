import os
import time
import psycopg

DATABASE_URL = os.getenv("DATABASE_URL")


def initialize_database():
    for attempt in range(15):
        try:
            with psycopg.connect(DATABASE_URL) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS incidents (
                        id BIGSERIAL PRIMARY KEY,
                        container_name VARCHAR(100) NOT NULL,
                        failure_type VARCHAR(100) NOT NULL,
                        detected_at TIMESTAMPTZ DEFAULT NOW(),
                        recovery_action VARCHAR(150),
                        recovery_duration_seconds DOUBLE PRECISION,
                        recovery_status VARCHAR(30),
                        recovery_attempts INTEGER DEFAULT 0
                    )
                """)
            print("Incident database initialized.", flush=True)
            return

        except Exception as error:
            print(f"Database connection attempt {attempt + 1}: {error}", flush=True)
            time.sleep(2)

    raise RuntimeError("Could not initialize incident database")


def record_incident(
    container_name,
    failure_type,
    recovery_action,
    duration,
    status,
    attempts
):
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("""
            INSERT INTO incidents (
                container_name,
                failure_type,
                recovery_action,
                recovery_duration_seconds,
                recovery_status,
                recovery_attempts
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            container_name,
            failure_type,
            recovery_action,
            duration,
            status,
            attempts
        ))

    print("Incident successfully saved to PostgreSQL.", flush=True)