# backend/scripts/import_tables.py
import csv
import sys
from pathlib import Path

from sqlalchemy import select, delete

# Allow running this file directly: add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.db import Base, SessionLocal, engine
from backend.core.db.models import Season, Team, TeamSeasonStats  # ✅ 建议从 models 导入，避免 core.db 未导出时报错

# ✅ 你的 CSV 实际在 backend/data 目录（按你的截图）
DATA_FILE = (
    Path(__file__).resolve().parents[2]  # backend/
    / "data"
    / "pl-tables-1993-2025.csv"          # ✅ 改成你实际文件名
).resolve()


def reset_stats_only():
    """
    只清空 standings（team_season_stats）数据，不删 users / seasons / teams。
    这样你不会每次导入都把 admin 用户清掉。
    """
    session = SessionLocal()
    try:
        session.execute(delete(TeamSeasonStats))
        session.commit()
        print("ℹ️ Cleared team_season_stats before import")
    finally:
        session.close()


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


def to_int(x: str, default: int = 0) -> int:
    try:
        return int(str(x).strip())
    except Exception:
        return default


def import_csv(reset_stats: bool = True):
    if reset_stats:
        reset_stats_only()

    if not DATA_FILE.exists():
        raise FileNotFoundError(f"CSV not found: {DATA_FILE}")

    session = SessionLocal()
    inserted, updated, skipped = 0, 0, 0

    try:
        with DATA_FILE.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # ✅ 跳过空行 / 缺字段行（你示例中有空行）
                if not row or not row.get("season_end_year") or not row.get("team"):
                    skipped += 1
                    continue

                end_year = to_int(row["season_end_year"], default=-1)
                team_name = row["team"].strip()
                if end_year <= 0 or not team_name:
                    skipped += 1
                    continue

                season = get_or_create_season(session, end_year)
                team = get_or_create_team(session, team_name)

                # ✅ Upsert：先查是否存在（根据 season_id + team_id 唯一）
                stmt = select(TeamSeasonStats).where(
                    TeamSeasonStats.season_id == season.id,
                    TeamSeasonStats.team_id == team.id
                )
                stats = session.execute(stmt).scalar_one_or_none()

                payload = dict(
                    position=to_int(row.get("position"), 0),
                    played=to_int(row.get("played"), 0),
                    won=to_int(row.get("won"), 0),
                    drawn=to_int(row.get("drawn"), 0),
                    lost=to_int(row.get("lost"), 0),
                    gf=to_int(row.get("gf"), 0),
                    ga=to_int(row.get("ga"), 0),
                    gd=to_int(row.get("gd"), to_int(row.get("gf"), 0) - to_int(row.get("ga"), 0)),
                    points=to_int(row.get("points"), 0),
                    notes=None,
                )

                if stats is None:
                    stats = TeamSeasonStats(
                        season_id=season.id,
                        team_id=team.id,
                        **payload
                    )
                    session.add(stats)
                    inserted += 1
                else:
                    for k, v in payload.items():
                        setattr(stats, k, v)
                    updated += 1

                # 可选：批量提交，避免一次导入太慢/太大
                if (inserted + updated) % 500 == 0:
                    session.commit()
                    print(f"... committed {inserted+updated} rows")

        session.commit()
        print(f"✅ Imported from {DATA_FILE}")
        print(f"   inserted={inserted}, updated={updated}, skipped={skipped}")

    except Exception as e:
        session.rollback()
        print("❌ Import failed:", e)
        raise
    finally:
        session.close()



def debug_preview_csv(n: int = 5):
    """
    调试用：打印 CSV 路径、表头、前 n 行内容
    """
    print("🔍 DEBUG CSV PREVIEW")
    print("CSV file:", DATA_FILE)

    if not DATA_FILE.exists():
        print("❌ CSV file does NOT exist!")
        return

    with DATA_FILE.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        print("📌 CSV headers:")
        print(reader.fieldnames)

        print(f"\n📌 First {n} rows:")
        for i, row in enumerate(reader):
            if i >= n:
                break
            print(f"Row {i+1}:")
            for k, v in row.items():
                print(f"  {k}: {v}")
            print("-" * 40)


if __name__ == "__main__":
    # 先看看 CSV 到底读到了什么
    debug_preview_csv(n=5)

    # 再真正导入（确认没问题后）
    import_csv(reset_stats=True)
