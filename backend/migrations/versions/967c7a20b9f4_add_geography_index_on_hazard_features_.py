"""add geography index on hazard_features geom

Revision ID: 967c7a20b9f4
Revises: 47edca22eabf
Create Date: 2026-10-09 18:33:42.341184

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '967c7a20b9f4'
down_revision = '47edca22eabf'
branch_labels = None
depends_on = None


def upgrade():
    # proximity queries cast geom to geography (distances in meters), which can't use
    # the plain geometry GIST index; this expression index matches geography(geom)
    op.create_index('idx_hazard_features_geog', 'hazard_features',
                    [sa.text('geography(geom)')], postgresql_using='gist')


def downgrade():
    op.drop_index('idx_hazard_features_geog', table_name='hazard_features')
