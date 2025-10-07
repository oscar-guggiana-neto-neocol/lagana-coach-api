"""Add courts table"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_courts"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "courts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("club_id", sa.Integer(), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("club_id", "name", name="uq_courts_club_name"),
    )
    op.create_index("ix_courts_club_id", "courts", ["club_id"])


def downgrade() -> None:
    op.drop_index("ix_courts_club_id", table_name="courts")
    op.drop_table("courts")
