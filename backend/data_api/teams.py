# backend/data_api/teams.py
from typing import List, Optional
from sqlalchemy import select, func

from .session import get_session
from .schemas import TeamMeta
from core.db import Team, TeamSeasonStats, Season

def list_all_teams() -> List[TeamMeta]:
    """返回数据库中所有球队（去重）"""
    with get_session() as session:
        stmt = select(Team).order_by(Team.name)
        teams = session.execute(stmt).scalars().all()
        return [TeamMeta(id=t.id, name=t.name) for t in teams]

def search_teams_by_keyword(keyword: str, limit: int = 20) -> List[TeamMeta]:
    """按关键字模糊搜索球队名"""
    pattern = f"%{keyword}%"
    with get_session() as session:
        stmt = (
            select(Team)
            .where(Team.name.ilike(pattern))
            .order_by(Team.name)
            .limit(limit)
        )
        teams = session.execute(stmt).scalars().all()
        return [TeamMeta(id=t.id, name=t.name) for t in teams]

def list_teams_in_season(end_year: int) -> List[TeamMeta]:
    """返回某赛季参加英超的所有球队列表"""
    with get_session() as session:
        stmt = (
            select(Team)
            .join(TeamSeasonStats, TeamSeasonStats.team_id == Team.id)
            .join(Season, TeamSeasonStats.season_id == Season.id)
            .where(Season.end_year == end_year)
            .group_by(Team.id)
            .order_by(Team.name)
        )
        teams = session.execute(stmt).scalars().all()
        return [TeamMeta(id=t.id, name=t.name) for t in teams]

def get_team_by_id(team_id: int) -> Optional[TeamMeta]:
    with get_session() as session:
        stmt = select(Team).where(Team.id == team_id)
        t = session.execute(stmt).scalar_one_or_none()
        if not t:
            return None
        return TeamMeta(id=t.id, name=t.name)
    

def get_team_by_name(name: str) -> Optional[TeamMeta]:
    with get_session() as session:
        stmt = select(Team).where(Team.name == name)
        t = session.execute(stmt).scalar_one_or_none()
        if not t:
            return None
        return TeamMeta(id=t.id, name=t.name)