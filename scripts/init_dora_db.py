import os
import time
import psycopg2
from psycopg2 import sql

def get_db_connection():
    """Establish connection to the PostgreSQL database."""
    # Retry logic for DB connection
    max_retries = 5
    for i in range(max_retries):
        try:
            return psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=os.getenv("POSTGRES_PORT", "5432"),
                database=os.getenv("POSTGRES_DB", "postgres"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres")
            )
        except psycopg2.OperationalError as e:
            if i < max_retries - 1:
                print(f"Database not ready, retrying in 2 seconds... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                raise e

def init_dora_db():
    """Initialize the DORA metrics database schema."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            print("Initializing DORA metrics tables...")
            
            # 1. Create dora_metrics table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dora_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_type VARCHAR(50) NOT NULL, -- 'deployment', 'lead_time', 'failure', 'restore'
                    value NUMERIC, -- The value of the metric (e.g., duration in minutes) or 1 for counting events
                    timestamp TIMESTAMP DEFAULT NOW(),
                    metadata JSONB -- Flexible field for extra context (commit_sha, version, etc.)
                );
            """)
            
            # Index for faster range queries on timestamp
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_dora_metrics_timestamp 
                ON dora_metrics (timestamp);
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_dora_metrics_type 
                ON dora_metrics (metric_type);
            """)

            # 2. Create dora_incidents table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dora_incidents (
                    id SERIAL PRIMARY KEY,
                    service VARCHAR(100) NOT NULL,
                    description TEXT,
                    severity VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
                    status VARCHAR(20) DEFAULT 'open', -- 'open', 'resolved'
                    start_time TIMESTAMP DEFAULT NOW(),
                    end_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            print("Tables created successfully.")
            conn.commit()
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    init_dora_db()
