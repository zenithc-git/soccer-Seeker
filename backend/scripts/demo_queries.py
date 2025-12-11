# backend/scripts/demo_queries.py
import sys
from pathlib import Path

from sqlalchemy import select

# Allow running this file directly: add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.db import SessionLocal, Season, Team, TeamSeasonStats


def print_standings(end_year: int):
    session = SessionLocal()
    try:
        stmt = (
            select(TeamSeasonStats, Team.name)
            .join(Season, TeamSeasonStats.season_id == Season.id)
            .join(Team, TeamSeasonStats.team_id == Team.id)
            .where(Season.end_year == end_year)
            .order_by(TeamSeasonStats.position)
        )
        print(f"=== Standings {end_year} ===")
        for stats, team_name in session.execute(stmt):
            print(f"{stats.position:>2}. {team_name:<20} Pts {stats.points}")
    finally:
        session.close()


if __name__ == "__main__":
    print_standings(2023)
