"""
Database setup script for local PostgreSQL.
Creates the 'atlas_ops' database if it doesn't exist.

Usage:
    python setup_db.py

Requires psycopg2: pip install psycopg2-binary
"""
import sys

def setup_database():
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)

    # ── Connection settings (match your pgAdmin setup) ──────────────────────
    DB_HOST = "localhost"
    DB_PORT = 5432
    DB_USER = "postgres"        # Change if your pgAdmin user is different
    DB_PASSWORD = "password"    # Change to your actual PostgreSQL password
    DB_NAME = "atlas_ops"

    print(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT} as '{DB_USER}'...")

    try:
        # Connect to default 'postgres' database to create our database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres",
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (DB_NAME,)
        )
        exists = cursor.fetchone()

        if exists:
            print(f"✅ Database '{DB_NAME}' already exists.")
        else:
            cursor.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"✅ Database '{DB_NAME}' created successfully!")

        cursor.close()
        conn.close()

        # Verify connection to the new database
        conn2 = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        conn2.close()
        print(f"✅ Successfully connected to '{DB_NAME}'.")
        print(f"\nDatabase URL for .env:")
        print(f"  DATABASE_URL=postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

    except psycopg2.OperationalError as e:
        print(f"\n❌ Could not connect to PostgreSQL!")
        print(f"   Error: {e}")
        print(f"\n   Ensure PostgreSQL is running and credentials are correct.")
        print(f"   Check pgAdmin → Server → Properties for host/port/username.")
        sys.exit(1)


if __name__ == "__main__":
    setup_database()
