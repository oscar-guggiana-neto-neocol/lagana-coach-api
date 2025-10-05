"""Initial schema"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role = postgresql.ENUM("admin", "coach", name="user_role", create_type=False)
    skill_level = postgresql.ENUM("beginner", "intermediate", "advanced", name="skill_level", create_type=False)
    lesson_type = postgresql.ENUM("club", "private", name="lesson_type", create_type=False)
    lesson_status = postgresql.ENUM("draft", "set", "executed", "invoiced", name="lesson_status", create_type=False)
    lesson_payment_status = postgresql.ENUM("open", "paid", name="lesson_payment_status", create_type=False)
    stroke_code = postgresql.ENUM(
        "forehand",
        "backhand",
        "volley",
        "smash",
        "serve",
        "lob",
        "drop_shot",
        "bandeja",
        "vibora",
        "chiquita",
        name="stroke_code",
        create_type=False,
    )
    invoice_status = postgresql.ENUM("draft", "issued", "paid", "void", name="invoice_status", create_type=False)

    user_role.create(op.get_bind(), checkfirst=True)
    skill_level.create(op.get_bind(), checkfirst=True)
    lesson_type.create(op.get_bind(), checkfirst=True)
    lesson_status.create(op.get_bind(), checkfirst=True)
    lesson_payment_status.create(op.get_bind(), checkfirst=True)
    stroke_code.create(op.get_bind(), checkfirst=True)
    invoice_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "coaches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50)),
        sa.Column("address_line1", sa.String(length=255)),
        sa.Column("address_line2", sa.String(length=255)),
        sa.Column("city", sa.String(length=100)),
        sa.Column("postcode", sa.String(length=20)),
        sa.Column("country", sa.String(length=100)),
        sa.Column("bank_name", sa.String(length=150)),
        sa.Column("account_holder_name", sa.String(length=150)),
        sa.Column("sort_code", sa.String(length=20)),
        sa.Column("account_number", sa.String(length=20)),
        sa.Column("iban", sa.String(length=34)),
        sa.Column("swift_bic", sa.String(length=11)),
        sa.Column("hourly_rate", sa.Numeric(10, 2)),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_coaches_id", "coaches", ["id"])

    op.create_table(
        "clubs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255)),
        sa.Column("phone", sa.String(length=50)),
        sa.Column("address_line1", sa.String(length=255)),
        sa.Column("address_line2", sa.String(length=255)),
        sa.Column("city", sa.String(length=100)),
        sa.Column("postcode", sa.String(length=20)),
        sa.Column("country", sa.String(length=100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255)),
        sa.Column("phone", sa.String(length=50)),
        sa.Column("birth_date", sa.Date()),
        sa.Column("skill_level", skill_level, nullable=False, server_default="beginner"),
        sa.Column("notes", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "strokes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", stroke_code, nullable=False, unique=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("coach_id", sa.Integer(), sa.ForeignKey("coaches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("club_id", sa.Integer(), sa.ForeignKey("clubs.id", ondelete="SET NULL")),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("type", lesson_type, nullable=False),
        sa.Column("status", lesson_status, nullable=False, server_default="draft"),
        sa.Column("payment_status", lesson_payment_status, nullable=False, server_default="open"),
        sa.Column("club_reimbursement_amount", sa.Numeric(10, 2)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("duration_minutes > 0", name="ck_lessons_duration_positive"),
        sa.CheckConstraint(
            "(club_reimbursement_amount IS NULL) OR (club_reimbursement_amount >= 0)",
            name="ck_lessons_reimbursement_positive",
        ),
    )
    op.create_index("ix_lessons_coach_date", "lessons", ["coach_id", "date"])

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("coach_id", sa.Integer(), sa.ForeignKey("coaches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("status", invoice_status, nullable=False, server_default="draft"),
        sa.Column("total_gross", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column(
            "total_club_reimbursement",
            sa.Numeric(12, 2),
            nullable=False,
            server_default="0",
        ),
        sa.Column("total_net", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("issued_at", sa.DateTime(timezone=True)),
        sa.Column("due_date", sa.Date()),
        sa.Column("pdf_url", sa.String(length=512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("token"),
    )

    op.create_table(
        "invoice_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="SET NULL")),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("metadata", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "player_coach",
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("coach_id", sa.Integer(), sa.ForeignKey("coaches.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_player_coach_player_id", "player_coach", ["player_id"])
    op.create_index("ix_player_coach_coach_id", "player_coach", ["coach_id"])

    op.create_table(
        "lesson_players",
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_lesson_players_lesson_id", "lesson_players", ["lesson_id"])
    op.create_index("ix_lesson_players_player_id", "lesson_players", ["player_id"])

    op.create_table(
        "lesson_strokes",
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("stroke_id", sa.Integer(), sa.ForeignKey("strokes.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_lesson_strokes_lesson_id", "lesson_strokes", ["lesson_id"])
    op.create_index("ix_lesson_strokes_stroke_id", "lesson_strokes", ["stroke_id"])
    op.create_unique_constraint("uq_lesson_stroke", "lesson_strokes", ["lesson_id", "stroke_id"])


def downgrade() -> None:
    op.drop_constraint("uq_lesson_stroke", "lesson_strokes", type_="unique")
    op.drop_index("ix_lesson_strokes_stroke_id", table_name="lesson_strokes")
    op.drop_index("ix_lesson_strokes_lesson_id", table_name="lesson_strokes")
    op.drop_table("lesson_strokes")

    op.drop_index("ix_lesson_players_player_id", table_name="lesson_players")
    op.drop_index("ix_lesson_players_lesson_id", table_name="lesson_players")
    op.drop_table("lesson_players")

    op.drop_index("ix_player_coach_coach_id", table_name="player_coach")
    op.drop_index("ix_player_coach_player_id", table_name="player_coach")
    op.drop_table("player_coach")

    op.drop_table("invoice_items")
    op.drop_table("password_reset_tokens")
    op.drop_table("invoices")
    op.drop_index("ix_lessons_coach_date", table_name="lessons")
    op.drop_table("lessons")
    op.drop_table("strokes")
    op.drop_table("players")
    op.drop_table("clubs")
    op.drop_table("coaches")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    postgresql.ENUM('draft', 'issued', 'paid', 'void', name='invoice_status').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM('forehand', 'backhand', 'volley', 'smash', 'serve', 'lob', 'drop_shot', 'bandeja', 'vibora', 'chiquita', name='stroke_code').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM('open', 'paid', name='lesson_payment_status').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM('draft', 'set', 'executed', 'invoiced', name='lesson_status').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM('club', 'private', name='lesson_type').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM('beginner', 'intermediate', 'advanced', name='skill_level').drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM('admin', 'coach', name='user_role').drop(op.get_bind(), checkfirst=True)
