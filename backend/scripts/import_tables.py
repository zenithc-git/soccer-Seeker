# backend/scripts/import_tables.py
import csv
import sys
from pathlib import Path

from sqlalchemy import select

# Allow running this file directly: add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.db import Base, SessionLocal, Season, Team, TeamSeasonStats, engine

DATA_FILE = (
    Path(__file__).resolve().parents[2]  # 回到项目根目录
    / "data"
    / "pl-tables-1993-2025.csv"
).resolve()


def reset_database():
    """Drop and recreate all tables so each import fully overwrites old data."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("ℹ️ Reset database tables before import")


def get_or_create_season(session, end_year: int):
    stmt = select(Season).where(Season.end_year == end_year)
    season = session.execute(stmt).scalar_one_or_none()
    if season:
        return season
    name = f"{end_year-1}-{end_year}"
    season = Season(end_year=end_year, name=name)
    session.add(season)
    session.flush()
    return season


def get_or_create_team(session, name: str):
    stmt = select(Team).where(Team.name == name)
    team = session.execute(stmt).scalar_one_or_none()
    if team:
        return team
    team = Team(name=name)
    session.add(team)
    session.flush()
    return team


def import_csv(reset: bool = True):
    if reset:
        reset_database()

    session = SessionLocal()
    try:
        with DATA_FILE.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                season = get_or_create_season(session, int(row["season_end_year"]))
                team = get_or_create_team(session, row["team"].strip())

                stats = TeamSeasonStats(
                    season_id=season.id,
                    team_id=team.id,
                    position=int(row["position"]),
                    played=int(row["played"]),
                    won=int(row["won"]),
                    drawn=int(row["drawn"]),
                    lost=int(row["lost"]),
                    gf=int(row["gf"]),
                    ga=int(row["ga"]),
                    gd=int(row["gd"]),
                    points=int(row["points"]),
                    notes=None,
                )
                session.add(stats)

        session.commit()
        print("✅ Imported from", DATA_FILE)
    except Exception as e:
        session.rollback()
        print("❌ Import failed:", e)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import_csv()
