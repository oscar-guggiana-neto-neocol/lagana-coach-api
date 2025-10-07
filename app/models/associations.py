from sqlalchemy import Column, DateTime, ForeignKey, Table, UniqueConstraint, func, Index

from app.db.base_class import Base

player_coach_table = Table(
    "player_coach",
    Base.metadata,
    Column("player_id", ForeignKey("players.id", ondelete="CASCADE"), primary_key=True),
    Column("coach_id", ForeignKey("coaches.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Index("ix_player_coach_player_id", "player_id"),
    Index("ix_player_coach_coach_id", "coach_id"),
)

lesson_players_table = Table(
    "lesson_players",
    Base.metadata,
    Column("lesson_id", ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
    Column("player_id", ForeignKey("players.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Index("ix_lesson_players_lesson_id", "lesson_id"),
    Index("ix_lesson_players_player_id", "player_id"),
)

lesson_strokes_table = Table(
    "lesson_strokes",
    Base.metadata,
    Column("lesson_id", ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
    Column("stroke_id", ForeignKey("strokes.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    UniqueConstraint("lesson_id", "stroke_id", name="uq_lesson_stroke"),
    Index("ix_lesson_strokes_lesson_id", "lesson_id"),
    Index("ix_lesson_strokes_stroke_id", "stroke_id"),
)

coach_club_table = Table(
    "coach_club_memberships",
    Base.metadata,
    Column("coach_id", ForeignKey("coaches.id", ondelete="CASCADE"), primary_key=True),
    Column("club_id", ForeignKey("clubs.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    UniqueConstraint("coach_id", "club_id", name="uq_coach_club"),
    Index("ix_coach_club_memberships_coach_id", "coach_id"),
    Index("ix_coach_club_memberships_club_id", "club_id"),
)

lesson_courts_table = Table(
    "lesson_courts",
    Base.metadata,
    Column("lesson_id", ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
    Column("court_id", ForeignKey("courts.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    UniqueConstraint("lesson_id", "court_id", name="uq_lesson_court"),
    Index("ix_lesson_courts_lesson_id", "lesson_id"),
    Index("ix_lesson_courts_court_id", "court_id"),
)
