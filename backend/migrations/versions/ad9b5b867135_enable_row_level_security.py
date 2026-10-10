"""enable row level security

Revision ID: ad9b5b867135
Revises: 967c7a20b9f4
Create Date: 2026-10-09 18:41:24.905354

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ad9b5b867135'
down_revision = '967c7a20b9f4'
branch_labels = None
depends_on = None

# Supabase serves every public table over its REST API (PostgREST) to anyone with the
# project's anon key. RLS with no policies denies those roles; the app connects as the
# table owner, which bypasses RLS. Harmless on a plain Postgres.
TABLES = ("hazard_features", "ingest_runs", "alembic_version")


def upgrade():
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade():
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
