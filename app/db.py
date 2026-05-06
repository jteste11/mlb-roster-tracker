from datetime import date, datetime
from pathlib import Path
from typing import Optional, Iterable

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

from .config import DB_PATH

Base = declarative_base()

def get_engine(db_path: Path = DB_PATH):
    return create_engine(f"sqlite:///{db_path}", echo=False, future=True)

SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    abbreviation = Column(String, nullable=True)

    rosters = relationship("Roster", back_populates="team")
    changes = relationship("RosterChange", back_populates="team")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    primary_position = Column(String, nullable=True)

    rosters = relationship("Roster", back_populates="player")
    changes = relationship("RosterChange", back_populates="player")


class Roster(Base):
    """
    Snapshot of a roster on a given date.
    """
    __tablename__ = "rosters"
    __table_args__ = (
        UniqueConstraint("date", "team_id", "player_id", name="uq_roster_date_team_player"),
    )

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    roster_type = Column(String, nullable=False, default="active")

    team = relationship("Team", back_populates="rosters")
    player = relationship("Player", back_populates="rosters")


class RosterChange(Base):
    """
    Tracks changes between consecutive roster snapshots.
    """
    __tablename__ = "roster_changes"

    id = Column(Integer, primary_key=True, index=True)
    change_date = Column(Date, nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    # "added" or "removed"
    change_type = Column(String, nullable=False)

    # Optional fields if you later track more detail
    old_roster_type = Column(String, nullable=True)
    new_roster_type = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    team = relationship("Team", back_populates="changes")
    player = relationship("Player", back_populates="changes")


def init_db():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()


def get_latest_roster_date_for_team(session: Session, team_id: int) -> Optional[date]:
    from sqlalchemy import select, func

    stmt = (
        select(func.max(Roster.date))
        .where(Roster.team_id == team_id)
    )
    result = session.execute(stmt).scalar_one_or_none()
    return result


def get_roster_for_team_on_date(session: Session, team_id: int, roster_date: date) -> list[Roster]:
    from sqlalchemy import select

    stmt = (
        select(Roster)
        .where(Roster.team_id == team_id)
        .where(Roster.date == roster_date)
    )
    return list(session.execute(stmt).scalars().all())
