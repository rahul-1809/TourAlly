"""
TourAlly — Migration Runner
Applies all SQL migration files in order against the Supabase PostgreSQL database.

Usage:
    cd backend
    python migrations/run_migrations.py
"""
import os
import sys
import glob
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# ─── Load environment ─────────────────────────────────────────
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌  DATABASE_URL not set in backend/.env")
    print("    Copy backend/.env.example → backend/.env and fill in your Supabase URL.")
    sys.exit(1)

# ─── Discover migration files ─────────────────────────────────
migrations_dir = Path(__file__).resolve().parent
sql_files = sorted(glob.glob(str(migrations_dir / "*.sql")))

if not sql_files:
    print("⚠️   No SQL migration files found in", migrations_dir)
    sys.exit(0)

# ─── Apply migrations ─────────────────────────────────────────
print(f"🔗  Connecting to database...")
try:
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            for sql_path in sql_files:
                name = Path(sql_path).name
                print(f"▶   Applying {name} ...", end=" ", flush=True)
                sql = Path(sql_path).read_text()
                try:
                    cur.execute(sql)
                    conn.commit()
                    print("✅  done")
                except Exception as e:
                    conn.rollback()
                    print(f"❌  FAILED\n    {e}")
                    sys.exit(1)

    print("\n✅  All migrations applied successfully.")

except psycopg.OperationalError as e:
    print(f"❌  Could not connect to database: {e}")
    sys.exit(1)
