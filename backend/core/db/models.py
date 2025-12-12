# backend/core/db/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Date, Enum
from sqlalchemy.orm import relationship
from .base import Base


class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True)
    end_year = Column(Integer, unique=True, nullable=False)   # 1993, 1998, ...
    name = Column(String, unique=True, nullable=False)        # "1992-1993"

    team_stats = relationship("TeamSeasonStats", back_populates="season")

    def __repr__(self):
        return f"<Season {self.name}>"


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    team_stats = relationship("TeamSeasonStats", back_populates="team")

    def __repr__(self):
        return f"<Team {self.name}>"


class TeamSeasonStats(Base):
    __tablename__ = "team_season_stats"
    __table_args__ = (
        UniqueConstraint("season_id", "team_id", name="uq_team_season"),
    )

    id = Column(Integer, primary_key=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    position = Column(Integer)
    played   = Column(Integer)
    won      = Column(Integer)
    drawn    = Column(Integer)
    lost     = Column(Integer)
    gf       = Column(Integer)
    ga       = Column(Integer)
    gd       = Column(Integer)
    points   = Column(Integer)
    notes    = Column(String)

    season = relationship("Season", back_populates="team_stats")
    team   = relationship("Team", back_populates="team_stats")

    def __repr__(self):
        return (
            f"<TeamSeasonStats season={self.season_id} "
            f"team={self.team_id} pos={self.position} pts={self.points}>"
        )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    birthday = Column(Date, nullable=True)
    role = Column(
        Enum("user", "vip_user", "admin", name="role_enum"),
        nullable=False,
        server_default="user",
    )
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"