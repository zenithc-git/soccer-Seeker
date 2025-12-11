# backend/data_api/standings.py
from typing import List
from sqlalchemy import select

from .session import get_session
from .schemas import TeamSeasonRow
from core.db import Season, Team, TeamSeasonStats

def get_standings_by_year(end_year: int) -> List[TeamSeasonRow]:
    """
    返回某个赛季的完整积分榜（每行是元数据对象 TeamSeasonRow）
    """
    with get_session() as session:
        stmt = (
            select(Season, Team, TeamSeasonStats)
            .join(TeamSeasonStats, TeamSeasonStats.season_id == Season.id)
            .join(Team, TeamSeasonStats.team_id == Team.id)
            .where(Season.end_year == end_year)
            .order_by(TeamSeasonStats.position)
        )
        rows = session.execute(stmt).all()

        result: List[TeamSeasonRow] = []
        for s, t, stats in rows:
            result.append(
                TeamSeasonRow(
                    season_end_year=s.end_year,
                    season_name=s.name,
                    team_id=t.id,
                    team_name=t.name,
                    position=stats.position,
                    played=stats.played,
                    won=stats.won,
                    drawn=stats.drawn,
                    lost=stats.lost,
                    gf=stats.gf,
                    ga=stats.ga,
                    gd=stats.gd,
                    points=stats.points,
                    notes=stats.notes,
                )
            )
        return result

def get_team_history(team_id: int) -> List[TeamSeasonRow]:
    """
    返回某球队历年在英超的联赛表现（每年一行）
    """
    with get_session() as session:
        stmt = (
            select(Season, Team, TeamSeasonStats)
            .join(TeamSeasonStats, TeamSeasonStats.season_id == Season.id)
            .join(Team, TeamSeasonStats.team_id == Team.id)
            .where(Team.id == team_id)
            .order_by(Season.end_year)
        )
        rows = session.execute(stmt).all()

        result: List[TeamSeasonRow] = []
        for s, t, stats in rows:
            result.append(
                TeamSeasonRow(
                    season_end_year=s.end_year,
                    season_name=s.name,
                    team_id=t.id,
                    team_name=t.name,
                    position=stats.position,
                    played=stats.played,
                    won=stats.won,
                    drawn=stats.drawn,
                    lost=stats.lost,
                    gf=stats.gf,
                    ga=stats.ga,
                    gd=stats.gd,
                    points=stats.points,
                    notes=stats.notes,
                )
            )
        return result
    
def get_team_season_stats(team_id: int, end_year: int) -> TeamSeasonRow:
    """
    返回某球队在某赛季的联赛表现
    """
    with get_session() as session:
        stmt = (
            select(Season, Team, TeamSeasonStats)
            .join(TeamSeasonStats, TeamSeasonStats.season_id == Season.id)
            .join(Team, TeamSeasonStats.team_id == Team.id)
            .where(Team.id == team_id, Season.end_year == end_year)
        )
        row = session.execute(stmt).one_or_none()
        if not row:
            raise ValueError(f"No data for team_id={team_id} in season ending {end_year}")

        s, t, stats = row
        return TeamSeasonRow(
            season_end_year=s.end_year,
            season_name=s.name,
            team_id=t.id,
            team_name=t.name,
            position=stats.position,
            played=stats.played,
            won=stats.won,
            drawn=stats.drawn,
            lost=stats.lost,
            gf=stats.gf,
            ga=stats.ga,
            gd=stats.gd,
            points=stats.points,
            notes=stats.notes,
        )

def get_top_n_teams(end_year: int, n: int) -> List[TeamSeasonRow]:
    """
    返回某赛季积分榜前N名球队的表现
    """
    with get_session() as session:
        stmt = (
            select(Season, Team, TeamSeasonStats)
            .join(TeamSeasonStats, TeamSeasonStats.season_id == Season.id)
            .join(Team, TeamSeasonStats.team_id == Team.id)
            .where(Season.end_year == end_year)
            .order_by(TeamSeasonStats.position)
            .limit(n)
        )
        rows = session.execute(stmt).all()

        result: List[TeamSeasonRow] = []
        for s, t, stats in rows:
            result.append(
                TeamSeasonRow(
                    season_end_year=s.end_year,
                    season_name=s.name,
                    team_id=t.id,
                    team_name=t.name,
                    position=stats.position,
                    played=stats.played,
                    won=stats.won,
                    drawn=stats.drawn,
                    lost=stats.lost,
                    gf=stats.gf,
                    ga=stats.ga,
                    gd=stats.gd,
                    points=stats.points,
                    notes=stats.notes,
                )
            )
        return result
    