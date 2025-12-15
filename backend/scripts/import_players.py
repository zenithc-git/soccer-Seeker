"""
Import player roster data into the players table.

Data source: data/epl_players_23_24(1).csv (tab-separated, includes teamID matching teams.id)
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, UniqueConstraint, delete

# Add project root to sys.path so `backend` is importable when running directly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.db import Base, SessionLocal, engine
from backend.core.db.models import Team, Player  # noqa: E402

DATA_FILE = PROJECT_ROOT / "data" / "epl_players_23_24.csv"


def parse_date(raw: str):
    """Parse YYYY/M/D (or similar) to date; return None if invalid."""
    if not raw:
        return None
    raw = raw.strip().replace("-", "/")
    try:
        return datetime.strptime(raw, "%Y/%m/%d").date()
    except Exception:
        try:
            return datetime.strptime(raw, "%Y/%m/%d").date()
        except Exception:
            return None


def reset_players():
    """Dangerous: wipe players table before import."""
    session = SessionLocal()
    try:
        session.execute(delete(Player))
        session.commit()
        print("🧹 Cleared players table.")
    finally:
        session.close()


def import_players(reset: bool = True):
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Player CSV not found: {DATA_FILE}")

    Base.metadata.create_all(engine)  # Ensure table exists

    if reset:
        reset_players()

    session = SessionLocal()
    inserted, updated, skipped = 0, 0, 0
    seen_keys = set()  # (team_id, first, last, shirt_no)
    try:
        with DATA_FILE.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=",")
            for row in reader:
                if not row or not row.get("teamID"):
                    skipped += 1
                    continue
                try:
                    team_id = int(row["teamID"])
                except Exception:
                    skipped += 1
                    continue

                team = session.get(Team, team_id)
                if not team:
                    print(f"⚠️ Skip player because team_id {team_id} not found: {row}")
                    skipped += 1
                    continue

                first = (row.get("firstName") or "").strip()
                last = (row.get("lastName") or "").strip()
                if not first and not last:
                    skipped += 1
                    continue

                shirt = row.get("shirtNo")
                try:
                    shirt_no = int(shirt) if shirt not in (None, "", "NA") else None
                except Exception:
                    shirt_no = None

                dedupe_key = (team_id, first, last, shirt_no)
                if dedupe_key in seen_keys:
                    skipped += 1
                    continue
                seen_keys.add(dedupe_key)

                stmt = select(Player).where(
                    Player.team_id == team_id,
                    Player.first_name == first,
                    Player.last_name == last,
                    Player.shirt_no == shirt_no,
                )
                player = session.execute(stmt).scalar_one_or_none()

                payload = dict(
                    birth_date=parse_date(row.get("birthDate") or ""),
                    position=(row.get("position") or "").strip(),
                )

                if player is None:
                    player = Player(
                        first_name=first,
                        last_name=last,
                        shirt_no=shirt_no,
                        team_id=team_id,
                        **payload,
                    )
                    session.add(player)
                    inserted += 1
                else:
                    for k, v in payload.items():
                        setattr(player, k, v)
                    updated += 1

                if (inserted + updated) % 500 == 0:
                    session.commit()
                    print(f"... committed {inserted+updated} players")

        session.commit()
        print(f"✅ Imported players from {DATA_FILE}")
        print(f"   inserted={inserted}, updated={updated}, skipped={skipped}")
    except Exception as e:
        session.rollback()
        print("❌ Import players failed:", e)
        raise
    finally:
        session.close()


def debug_preview(n: int = 5):
    print("CSV file:", DATA_FILE)
    if not DATA_FILE.exists():
        print("❌ file missing")
        return
    with DATA_FILE.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter="\t")
        print("Headers:", reader.fieldnames)
        for i, row in enumerate(reader):
            if i >= n:
                break
            print(row)


if __name__ == "__main__":
    debug_preview()
    import_players(reset=True)
