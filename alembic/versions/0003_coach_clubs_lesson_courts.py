"""Coach club memberships and lesson courts"""

from alembic import op
import sqlalchemy as sa


revision = "0003_coach_clubs_lesson_courts"
down_revision = "0002_add_courts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "coach_club_memberships",
        sa.Column("coach_id", sa.Integer(), sa.ForeignKey("coaches.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("club_id", sa.Integer(), sa.ForeignKey("clubs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("coach_id", "club_id", name="uq_coach_club"),
    )
    op.create_index("ix_coach_club_memberships_coach_id", "coach_club_memberships", ["coach_id"])
    op.create_index("ix_coach_club_memberships_club_id", "coach_club_memberships", ["club_id"])

    op.add_column("coaches", sa.Column("default_club_id", sa.Integer(), sa.ForeignKey("clubs.id", ondelete="SET NULL")))
    op.create_index("ix_coaches_default_club_id", "coaches", ["default_club_id"])

    op.create_table(
        "lesson_courts",
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("court_id", sa.Integer(), sa.ForeignKey("courts.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("lesson_id", "court_id", name="uq_lesson_court"),
    )
    op.create_index("ix_lesson_courts_lesson_id", "lesson_courts", ["lesson_id"])
    op.create_index("ix_lesson_courts_court_id", "lesson_courts", ["court_id"])


def downgrade() -> None:
    op.drop_index("ix_lesson_courts_court_id", table_name="lesson_courts")
    op.drop_index("ix_lesson_courts_lesson_id", table_name="lesson_courts")
    op.drop_table("lesson_courts")

    op.drop_index("ix_coaches_default_club_id", table_name="coaches")
    op.drop_column("coaches", "default_club_id")

    op.drop_index("ix_coach_club_memberships_club_id", table_name="coach_club_memberships")
    op.drop_index("ix_coach_club_memberships_coach_id", table_name="coach_club_memberships")
    op.drop_table("coach_club_memberships")
