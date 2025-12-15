# backend/core/db/models.py
from sqlalchemy import (
    Column, Integer, String, ForeignKey, UniqueConstraint, Date, Enum, Index
)
from sqlalchemy.orm import relationship
from .base import Base


class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    end_year = Column(Integer, unique=True, nullable=False, index=True)   # 1993, 1998, ...
    name = Column(String, unique=True, nullable=False)                    # "1992-1993"

    team_stats = relationship(
        "TeamSeasonStats",
        back_populates="season",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Season {self.name}>"


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)

    team_stats = relationship(
        "TeamSeasonStats",
        back_populates="team",
        cascade="all, delete-orphan"
    )
    players = relationship(
        "Player",
        back_populates="team",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Team {self.name}>"


class TeamSeasonStats(Base):
    __tablename__ = "team_season_stats"
    __table_args__ = (
        UniqueConstraint("season_id", "team_id", name="uq_team_season"),
        # 常用查询：赛季榜单/排序
        Index("ix_team_season_stats_season_pos", "season_id", "position"),
        Index("ix_team_season_stats_season_points", "season_id", "points"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    position = Column(Integer, nullable=False)
    played   = Column(Integer, nullable=False)
    won      = Column(Integer, nullable=False)
    drawn    = Column(Integer, nullable=False)
    lost     = Column(Integer, nullable=False)
    gf       = Column(Integer, nullable=False)
    ga       = Column(Integer, nullable=False)
    gd       = Column(Integer, nullable=False)
    points   = Column(Integer, nullable=False)

    notes    = Column(String, nullable=True)

    season = relationship("Season", back_populates="team_stats")
    team   = relationship("Team", back_populates="team_stats")

    def __repr__(self):
        return (
            f"<TeamSeasonStats season={self.season_id} "
            f"team={self.team_id} pos={self.position} pts={self.points}>"
        )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    birthday = Column(Date, nullable=True)
    role = Column(
        Enum("user", "vip_user", "admin", name="role_enum"),
        nullable=False,
        server_default="user",
    )
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint("team_id", "first_name", "last_name", "shirt_no", name="uq_team_player_unique"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    shirt_no = Column(Integer, nullable=True)
    birth_date = Column(Date, nullable=True)
    position = Column(String, nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)

    team = relationship("Team", back_populates="players")

    def __repr__(self):
        return f"<Player {self.first_name} {self.last_name} team={self.team_id} no={self.shirt_no}>"
