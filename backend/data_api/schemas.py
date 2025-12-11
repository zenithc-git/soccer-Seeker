# backend/data_api/schemas.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class SeasonMeta:
    id: int
    end_year: int
    name: str

@dataclass
class TeamMeta:
    id: int
    name: str

@dataclass
class TeamSeasonRow:
    """积分榜中的一行元数据"""
    season_end_year: int
    season_name: str
    team_id: int
    team_name: str

    position: int
    played: int
    won: int
    drawn: int
    lost: int
    gf: int
    ga: int
    gd: int
    points: int
    notes: Optional[str] = None