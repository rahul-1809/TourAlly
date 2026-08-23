"""
TourAlly — Supabase Connection Test
Verifies DATABASE_URL is reachable and both app tables exist.

Usage:
    cd backend
    python migrations/test_connection.py
"""
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌  DATABASE_URL not set. Copy .env.example → .env and fill in your values.")
    sys.exit(1)

print("🔗  Testing connection to Supabase...")

try:
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # Basic connectivity
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"✅  Connected!  PostgreSQL: {version[:40]}...")

            # Check app tables exist
            for table in ("travel_sessions", "agent_run_logs"):
                cur.execute(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s);",
                    (table,),
                )
                exists = cur.fetchone()[0]
                status = "✅" if exists else "⚠️  (run migrations/run_migrations.py first)"
                print(f"    Table '{table}': {status}")

    print("\n🎉  Connection test passed!")

except psycopg.OperationalError as e:
    print(f"❌  Connection failed: {e}")
    sys.exit(1)
