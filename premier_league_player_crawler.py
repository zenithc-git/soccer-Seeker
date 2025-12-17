"""
Premier League player crawler.

Targets the Premier League site data API (footballapi.pulselive.com) to pull the
player directory plus a handful of profile details and the headshot image link.

Collected fields:
    player_id, name, first_name, last_name, club, position, shirt_number,
    nationality, country_code, preferred_foot, date_of_birth, appearances,
    goals, assists, detail_url, headshot_url, local_image_path (if downloaded).

Outputs:
    data/epl_players_{season}.json
    data/epl_players_{season}.csv
    data/player_photos/ (optional, when --download-images is set)

Run example:
    python premier_league_player_crawler.py --season 2025 --competition 8 --download-images
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
import typing as t

import requests

BASE_API = "https://footballapi.pulselive.com/football"
LIST_API = f"{BASE_API}/players"
DETAIL_API = f"{BASE_API}/players/{{player_id}}"
STATS_API = f"{BASE_API}/players/{{player_id}}/stats"

# Headers mimic the site so we are treated as a normal browser.
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Origin": "https://www.premierleague.com",
    "Referer": "https://www.premierleague.com/",
    "Accept": "application/json, text/plain, */*",
}


def request_json(
    session: requests.Session,
    url: str,
    params: dict[str, t.Any] | None = None,
    *,
    max_retries: int = 3,
    retry_backoff: float = 1.5,
) -> dict[str, t.Any]:
    """GET a URL and return JSON with minimal retry handling."""
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            resp = session.get(url, params=params, timeout=15)
            if resp.status_code == 429 and attempt < max_retries - 1:
                # Simple backoff on rate limit.
                time.sleep(retry_backoff * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(retry_backoff * (attempt + 1))
    raise RuntimeError(f"Failed to request {url} after retries: {last_error}")


def fetch_player_list_page(
    session: requests.Session,
    competition_id: int,
    season: int,
    page: int,
    page_size: int,
    comps_code: str | None = None,
) -> tuple[list[dict[str, t.Any]], int]:
    """Fetch one page of the player directory and return content + num_pages."""
    params = {
        "page": page,
        "pageSize": page_size,
        "comps": competition_id,
        "season": season,
    }
    if comps_code:
        params["compsCode"] = comps_code
    data = request_json(session, LIST_API, params=params)
    content = data.get("content") or []
    page_info = data.get("pageInfo") or {}
    num_pages = int(page_info.get("numPages") or 0)
    return content, num_pages


def fetch_player_detail(
    session: requests.Session,
    competition_id: int,
    player_id: int,
    comps_code: str | None = None,
) -> dict[str, t.Any]:
    """Fetch profile detail for a player."""
    params = {"comps": competition_id}
    if comps_code:
        params["compsCode"] = comps_code
    return request_json(session, DETAIL_API.format(player_id=player_id), params=params)


def fetch_player_history(
    session: requests.Session,
    player_id: int,
) -> dict[str, t.Any]:
    """Fetch player history summary (provides appearances/goals/assists)."""
    url = f"{BASE_API}/players/{player_id}/history"
    try:
        return request_json(session, url)
    except RuntimeError:
        return {}


def fetch_player_stats(
    session: requests.Session,
    competition_id: int,
    player_id: int,
    comps_code: str | None = None,
) -> list[dict[str, t.Any]]:
    """Fetch aggregate stats used on the profile page (apps/goals/assists)."""
    params = {"comps": competition_id}
    if comps_code:
        params["compsCode"] = comps_code
    try:
        data = request_json(
            session, STATS_API.format(player_id=player_id), params=params
        )
        return data.get("stats") or []
    except RuntimeError as exc:
        # Some players (youth/new signings) return 404 for stats; treat as empty.
        if "404" in str(exc):
            return []
        raise


def build_headshot_url(opta_id: str | int | None, size: str = "250x250") -> str | None:
    """Return the standard Premier League headshot URL."""
    if not opta_id:
        return None
    # Opta IDs are already padded; treat as string to preserve leading zeros.
    return f"https://resources.premierleague.com/premierleague/photos/players/{size}/p{opta_id}.png"


def find_stat(stats: list[dict[str, t.Any]], candidates: list[str]) -> t.Any:
    """Grab the first matching stat value by name."""
    for name in candidates:
        for item in stats:
            if item.get("name") == name:
                return item.get("value")
    return None


def slugify(text: str) -> str:
    """Simple filename-safe slug."""
    keep = []
    for ch in text:
        if ch.isalnum():
            keep.append(ch.lower())
        elif ch in (" ", "-", "_"):
            keep.append("-")
    slug = "".join(keep).strip("-")
    return slug or "player"


def download_image(
    session: requests.Session,
    url: str,
    dest_dir: str,
    filename: str,
) -> str | None:
    """Download an image to disk; returns the saved path on success."""
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, filename)
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        return dest_path
    except Exception:
        return None


def normalize_player_record(
    list_item: dict[str, t.Any],
    detail: dict[str, t.Any],
    history: dict[str, t.Any],
    stats: list[dict[str, t.Any]],
    competition_id: int,
    download_images: bool,
    session: requests.Session,
    photo_dir: str,
) -> dict[str, t.Any]:
    """Merge list item + detail + stats into one flattened record."""
    info = detail.get("info") or {}
    list_info = list_item.get("info") or {}
    name_obj = detail.get("name") or list_item.get("name") or {}
    history_name = history.get("name") or {}

    def pick(*values: t.Any) -> t.Any:
        for v in values:
            if v not in (None, "", []):
                return v
        return None

    current_team = pick(
        detail.get("currentTeam"),
        list_item.get("currentTeam"),
        list_item.get("club"),
    ) or {}
    alt_ids = pick(detail.get("altIds"), list_item.get("altIds")) or {}

    player_id = detail.get("id") or list_item.get("id") or history.get("id")
    display_name = (
        name_obj.get("display")
        or name_obj.get("full")
        or history_name.get("display")
        or history_name.get("full")
        or ""
    )
    first_name = name_obj.get("first") or history_name.get("first") or ""
    last_name = name_obj.get("last") or history_name.get("last") or ""

    detail_birth = info.get("birth") or detail.get("birth") or history.get("birth") or {}
    list_birth = list_info.get("birth") or {}
    detail_country = (detail_birth.get("country") or {}) if isinstance(detail_birth, dict) else {}
    list_country = (list_birth.get("country") or {}) if isinstance(list_birth, dict) else {}
    national_team = detail.get("nationalTeam") or list_item.get("nationalTeam") or {}
    if isinstance(national_team, list):
        national_team = national_team[0] if national_team else {}
    if isinstance(national_team, str):
        national_team_country = {"name": national_team}
    elif isinstance(national_team, dict):
        nat_country = national_team.get("country") or {}
        if isinstance(nat_country, dict):
            national_team_country = nat_country
        else:
            national_team_country = {
                "name": national_team.get("country") if isinstance(national_team.get("country"), str) else None,
                "alpha2": national_team.get("isoCode"),
            }
    else:
        national_team_country = {}

    nationality = pick(
        info.get("nationality"),
        detail_country.get("country"),
        list_country.get("country"),
        national_team_country.get("name"),
        history.get("nationalTeam", {}).get("country") if isinstance(history.get("nationalTeam"), dict) else None,
    ) or ""
    country_code = pick(
        info.get("nation"),
        detail_country.get("alpha2"),
        list_country.get("alpha2"),
        national_team_country.get("alpha2"),
        info.get("nationalityCode"),
        history.get("nationalTeam", {}).get("isoCode") if isinstance(history.get("nationalTeam"), dict) else None,
    )

    opta_id = pick(
        alt_ids.get("opta") if isinstance(alt_ids, dict) else None,
        alt_ids.get("optaId") if isinstance(alt_ids, dict) else None,
        alt_ids.get("optaIdv2") if isinstance(alt_ids, dict) else None,
    )
    headshot_url = build_headshot_url(opta_id)
    preferred_foot = pick(
        info.get("foot"),
        info.get("preferredFoot"),
        list_info.get("foot"),
        list_info.get("preferredFoot"),
        history.get("foot"),
    )
    dob_label = pick(
        (detail_birth.get("date") or {}).get("label") if isinstance(detail_birth, dict) else None,
        (list_birth.get("date") or {}).get("label") if isinstance(list_birth, dict) else None,
    )

    appearances = pick(
        find_stat(stats, ["appearances"]),
        history.get("appearances"),
        list_item.get("appearances"),
        list_info.get("appearances"),
    )
    goals = pick(
        find_stat(stats, ["goals"]),
        history.get("goals"),
        list_item.get("goals"),
        list_info.get("goals"),
    )
    assists = pick(
        find_stat(stats, ["goal_assist", "goalAssists", "assists"]),
        history.get("assists"),
        list_item.get("assists"),
        list_info.get("assists"),
    )

    local_image_path = None
    if download_images and headshot_url:
        filename = f"{player_id}_{slugify(display_name)}.png"
        local_image_path = download_image(session, headshot_url, photo_dir, filename)

    return {
        "player_id": player_id,
        "name": display_name,
        "first_name": first_name,
        "last_name": last_name,
        "club": current_team.get("name") or current_team.get("clubName"),
        "position": pick(
            info.get("position"),
            info.get("positionInfo"),
            list_info.get("position"),
            list_info.get("positionInfo"),
            list_item.get("position"),
        ),
        "shirt_number": pick(
            info.get("shirtNum"),
            info.get("shirtNumber"),
            list_info.get("shirtNum"),
            list_info.get("shirtNumber"),
            list_item.get("shirtNumber"),
        ),
        "nationality": nationality,
        "country_code": country_code,
        "preferred_foot": preferred_foot,
        "date_of_birth": dob_label,
        "appearances": appearances,
        "goals": goals,
        "assists": assists,
        "detail_url": f"https://www.premierleague.com/players/{player_id}",
        "headshot_url": headshot_url,
        "local_image_path": local_image_path,
        "competition_id": competition_id,
    }


def crawl_players(
    competition_id: int,
    season: int,
    *,
    page_size: int = 30,
    sleep: float = 0.4,
    download_images: bool = False,
    limit: int | None = None,
    verbose: bool = False,
    max_pages: int | None = None,
    comps_code: str | None = None,
    require_club: bool = True,
) -> list[dict[str, t.Any]]:
    """Crawl every player in the directory for the given competition/season."""
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    results: list[dict[str, t.Any]] = []
    page = 0
    num_pages = 1
    photo_dir = os.path.join("data", "player_photos")
    if verbose:
        print(
            f"[START] comps={competition_id} compsCode={comps_code or '-'} "
            f"season={season} page_size={page_size} limit={limit} max_pages={max_pages}",
            flush=True,
        )

    while page < num_pages:
        if max_pages is not None and page >= max_pages:
            break
        content, num_pages = fetch_player_list_page(
            session, competition_id, season, page, page_size, comps_code
        )
        if not content:
            break
        if verbose:
            print(
                f"[PAGE] page {page+1}/{num_pages} · received {len(content)} rows",
                flush=True,
            )

        for item in content:
            raw_id = item.get("id")
            try:
                player_id = int(raw_id)
            except Exception:
                # Skip entries that do not have a valid numeric ID.
                continue
            if player_id <= 0:
                continue
            try:
                detail = fetch_player_detail(session, competition_id, player_id, comps_code)
            except RuntimeError as exc:
                # Some historic/placeholder entries return 404 on detail; skip them.
                if verbose:
                    print(f"[SKIP] detail missing for player_id={player_id}: {exc}", flush=True)
                continue
            stats_id = (
                detail.get("playerId")
                or detail.get("id")
                or player_id
            )
            history = fetch_player_history(session, player_id)
            try:
                stats_id_int = int(stats_id)
            except Exception:
                stats_id_int = player_id
            try:
                stats = fetch_player_stats(session, competition_id, stats_id_int, comps_code)
            except RuntimeError as exc:
                # Network/proxy/404 issues on stats should not stop the crawl.
                if verbose:
                    print(
                        f"[SKIP] stats missing for player_id={player_id} stats_id={stats_id_int}: {exc}",
                        flush=True,
                    )
                stats = []
            record = normalize_player_record(
                item, detail, history, stats, competition_id, download_images, session, photo_dir
            )
            if require_club and not record.get("club"):
                # Skip free agents / retired entries when a club is required.
                continue
            results.append(record)
            if verbose:
                print(
                    f"[PLAYER] #{len(results):03d} {record.get('name','')} "
                    f"({record.get('club','-')})",
                    flush=True,
                )
            if limit and len(results) >= limit:
                return results
            time.sleep(sleep)

        page += 1
        time.sleep(sleep)

    return results


def save_outputs(players: list[dict[str, t.Any]], season: int, out_dir: str = "data") -> None:
    """Persist players to JSON and CSV."""
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, f"epl_players_{season}.json")
    csv_path = os.path.join(out_dir, f"epl_players_{season}.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False, indent=2)

    fieldnames: list[str] = []
    if players:
        # Preserve a stable column order.
        preferred_order = [
            "player_id",
            "name",
            "first_name",
            "last_name",
            "club",
            "position",
            "shirt_number",
            "nationality",
            "country_code",
            "preferred_foot",
            "date_of_birth",
            "appearances",
            "goals",
            "assists",
            "detail_url",
            "headshot_url",
            "local_image_path",
            "competition_id",
        ]
        fieldnames = preferred_order
    else:
        fieldnames = ["player_id", "name", "club"]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in players:
            writer.writerow(row)

    print(f"[INFO] Saved JSON to {json_path}")
    print(f"[INFO] Saved CSV  to {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape Premier League players for a competition + season."
    )
    parser.add_argument(
        "--competition",
        type=int,
        default=1,
        help="Competition ID (Premier League main comp is usually 1).",
    )
    parser.add_argument(
        "--comps-code",
        type=str,
        default="PL",
        help="Competition code string (e.g., PL).",
    )
    parser.add_argument(
        "--season",
        type=int,
        default=2025,
        help="Season year, e.g. 2025 for 2025/26.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=40,
        help="Page size for list endpoint.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Stop after N players (for quick tests).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-page and per-player progress.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Stop after N pages (debug).",
    )
    parser.add_argument(
        "--no-require-club",
        action="store_true",
        help="Keep players even if no current club is present in the API.",
    )
    parser.add_argument(
        "--download-images",
        action="store_true",
        help="Download headshot PNGs into data/player_photos.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.4,
        help="Delay between requests in seconds to be polite to the API.",
    )
    args = parser.parse_args()

    players = crawl_players(
        competition_id=args.competition,
        season=args.season,
        page_size=args.page_size,
        sleep=args.sleep,
        download_images=args.download_images,
        limit=args.limit,
        verbose=args.verbose,
        max_pages=args.max_pages,
        comps_code=args.comps_code,
        require_club=not args.no_require_club,
    )
    save_outputs(players, args.season)
    print(f"[DONE] Crawled {len(players)} players.")


if __name__ == "__main__":
    main()
