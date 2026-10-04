"""human review workflow

Revision ID: 20260802_0002
Revises: 43496331c0dd
Create Date: 2026-08-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260802_0002"
down_revision: Union[str, Sequence[str], None] = "43496331c0dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _table_names() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return set(inspector.get_table_names())


def _index_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if column.name not in _column_names(table_name):
        op.add_column(table_name, column)


def upgrade() -> None:
    _add_column_if_missing("datasets", sa.Column("metadata_json", sa.JSON(), nullable=True))
    _add_column_if_missing("datasets", sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing("datasets", sa.Column("locked_by_id", sa.Integer(), nullable=True))

    _add_column_if_missing("ground_truth_pages", sa.Column("image_path", sa.String(length=1000), nullable=True))
    _add_column_if_missing("ground_truth_pages", sa.Column("image_width", sa.Integer(), nullable=True))
    _add_column_if_missing("ground_truth_pages", sa.Column("image_height", sa.Integer(), nullable=True))
    _add_column_if_missing("ground_truth_pages", sa.Column("metadata_json", sa.JSON(), nullable=True))

    _add_column_if_missing("ground_truth_lines", sa.Column("draft_text", sa.Text(), nullable=True))
    _add_column_if_missing("ground_truth_lines", sa.Column("text_reviewed", sa.Boolean(), server_default=sa.false(), nullable=False))
    _add_column_if_missing("ground_truth_lines", sa.Column("bbox_reviewed", sa.Boolean(), server_default=sa.false(), nullable=False))
    _add_column_if_missing("ground_truth_lines", sa.Column("text_changed", sa.Boolean(), server_default=sa.false(), nullable=False))
    _add_column_if_missing("ground_truth_lines", sa.Column("bbox_changed", sa.Boolean(), server_default=sa.false(), nullable=False))
    _add_column_if_missing("ground_truth_lines", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing("ground_truth_lines", sa.Column("review_action_id", sa.String(length=64), nullable=True))

    with op.batch_alter_table("processing_jobs") as batch_op:
        batch_op.alter_column("document_id", existing_type=sa.Integer(), nullable=True)
        processing_job_columns = _column_names("processing_jobs")
        if "progress" not in processing_job_columns:
            batch_op.add_column(sa.Column("progress", sa.Float(), server_default="0", nullable=False))
        if "result_path" not in processing_job_columns:
            batch_op.add_column(sa.Column("result_path", sa.String(length=1000), nullable=True))

    if "ground_truth_review_audits" not in _table_names():
        op.create_table(
            "ground_truth_review_audits",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("dataset_id", sa.Integer(), nullable=False),
            sa.Column("page_id", sa.Integer(), nullable=False),
            sa.Column("line_id", sa.Integer(), nullable=True),
            sa.Column("reviewer_id", sa.Integer(), nullable=False),
            sa.Column("reviewer_display_name", sa.String(length=255), nullable=False),
            sa.Column("action", sa.String(length=80), nullable=False),
            sa.Column("previous_text", sa.Text(), nullable=True),
            sa.Column("new_text", sa.Text(), nullable=True),
            sa.Column("text_changed", sa.Boolean(), nullable=False),
            sa.Column("previous_bbox", sa.JSON(), nullable=True),
            sa.Column("new_bbox", sa.JSON(), nullable=True),
            sa.Column("bbox_changed", sa.Boolean(), nullable=False),
            sa.Column("source_image_hash", sa.String(length=64), nullable=True),
            sa.Column("review_action_id", sa.String(length=64), nullable=False),
            sa.Column("dataset_version", sa.String(length=50), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
            sa.ForeignKeyConstraint(["line_id"], ["ground_truth_lines.id"]),
            sa.ForeignKeyConstraint(["page_id"], ["ground_truth_pages.id"]),
            sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    review_audit_indexes = _index_names("ground_truth_review_audits")
    if op.f("ix_ground_truth_review_audits_id") not in review_audit_indexes:
        op.create_index(op.f("ix_ground_truth_review_audits_id"), "ground_truth_review_audits", ["id"], unique=False)
    if op.f("ix_ground_truth_review_audits_review_action_id") not in review_audit_indexes:
        op.create_index(op.f("ix_ground_truth_review_audits_review_action_id"), "ground_truth_review_audits", ["review_action_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_ground_truth_review_audits_review_action_id"), table_name="ground_truth_review_audits")
    op.drop_index(op.f("ix_ground_truth_review_audits_id"), table_name="ground_truth_review_audits")
    op.drop_table("ground_truth_review_audits")
    with op.batch_alter_table("processing_jobs") as batch_op:
        batch_op.drop_column("result_path")
        batch_op.drop_column("progress")
        batch_op.alter_column("document_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("ground_truth_lines", "review_action_id")
    op.drop_column("ground_truth_lines", "reviewed_at")
    op.drop_column("ground_truth_lines", "bbox_changed")
    op.drop_column("ground_truth_lines", "text_changed")
    op.drop_column("ground_truth_lines", "bbox_reviewed")
    op.drop_column("ground_truth_lines", "text_reviewed")
    op.drop_column("ground_truth_lines", "draft_text")
    op.drop_column("ground_truth_pages", "metadata_json")
    op.drop_column("ground_truth_pages", "image_height")
    op.drop_column("ground_truth_pages", "image_width")
    op.drop_column("ground_truth_pages", "image_path")
    op.drop_column("datasets", "locked_by_id")
    op.drop_column("datasets", "locked_at")
    op.drop_column("datasets", "metadata_json")
