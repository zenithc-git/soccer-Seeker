# backend/data_api/seasons.py
from typing import List, Optional
from sqlalchemy import select

from .session import get_session
from .schemas import SeasonMeta
from core.db import Season   # ORM 模型

def list_seasons() -> List[SeasonMeta]:
    """按 end_year 升序返回所有赛季元数据"""
    with get_session() as session:
        stmt = select(Season).order_by(Season.end_year)
        seasons = session.execute(stmt).scalars().all()
        return [
            SeasonMeta(id=s.id, end_year=s.end_year, name=s.name)
            for s in seasons
        ]

def get_season_by_year(end_year: int) -> Optional[SeasonMeta]:
    """根据赛季结束年份获取赛季元数据"""
    with get_session() as session:
        stmt = select(Season).where(Season.end_year == end_year)
        s = session.execute(stmt).scalar_one_or_none()
        if not s:
            return None
        return SeasonMeta(id=s.id, end_year=s.end_year, name=s.name)
    
def get_season_by_team_season_stats_id(stats_id: int) -> Optional[SeasonMeta]:
    """根据 TeamSeasonStats 的 ID 获取对应的赛季元数据"""
    with get_session() as session:
        stmt = (
            select(Season)
            .join(TeamSeasonStats, TeamSeasonStats.season_id == Season.id)
            .where(TeamSeasonStats.id == stats_id)
        )
        s = session.execute(stmt).scalar_one_or_none()
        if not s:
            return None
        return SeasonMeta(id=s.id, end_year=s.end_year, name=s.name)
    
def get_season_by_id(season_id: int) -> Optional[SeasonMeta]:
    """根据赛季 ID 获取赛季元数据"""
    with get_session() as session:
        stmt = select(Season).where(Season.id == season_id)
        s = session.execute(stmt).scalar_one_or_none()
        if not s:
            return None
        return SeasonMeta(id=s.id, end_year=s.end_year, name=s.name)