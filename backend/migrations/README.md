# Database Migrations and Checkpointer Setup

This folder contains SQL schemas and helpers to initialize the checkpoint database for TourAlly's LangGraph multi-agent persistence.

## 🗄️ Checkpointer Persistence Model

TourAlly uses a database checkpointer to save execution states (checkpoints, interrupts, inputs, and outputs) between runs. This supports human-in-the-loop (HITL) workflows:
- The backend parses the database connection string (`DATABASE_URL`).
- If valid, it instantiates `PostgresSaver` to serialize state.
- If invalid or offline, the system falls back to a global `MemorySaver` checkpointer.

---

## 🚀 Running Migrations

Migrations are stored as raw SQL files. To apply them to your Supabase PostgreSQL instance:

1. **Configure your Database URL**: Ensure `DATABASE_URL` is set in your `backend/.env` file. You should use the **direct connection string** (not transaction pooler).
2. **Execute the Migration Script**:
   Navigate to the `backend` directory and run:
   ```bash
   python migrations/run_migrations.py
   ```

The script will read the files sequentially, apply table schemas, and verify that the Postgres Saver checkpointer tables exist and are properly configured.
