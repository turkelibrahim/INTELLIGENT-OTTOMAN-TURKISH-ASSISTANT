"""add_version_fields_to_processing_job

Revision ID: faeb2ae3d080
Revises: 5803844cde74
Create Date: 2026-08-03 23:05:36.528924
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = 'faeb2ae3d080'
down_revision: Union[str, Sequence[str], None] = '5803844cde74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("processing_jobs", sa.Column("pipeline_version", sa.String(length=50), nullable=True))
    op.add_column("processing_jobs", sa.Column("worker_version", sa.String(length=50), nullable=True))

def downgrade() -> None:
    with op.batch_alter_table("processing_jobs") as batch_op:
        batch_op.drop_column("worker_version")
        batch_op.drop_column("pipeline_version")
