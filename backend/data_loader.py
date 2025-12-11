# backend/data_loader.py
import os
import pandas as pd

# 计算 CSV 路径：../data/pl-tables-1993-2024.csv
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "pl-tables-1993-2024.csv")

_STANDINGS_DF = None


def load_standings_df():
    df = pd.read_csv(CSV_PATH)

    # 按你的实际列名修改这里：
    # 例如：season_en, team, position, played, won, drawn, lost, gf, ga, gd, points
    df["season_en"] = df["season_en"].astype(int)
    df["position"] = df["position"].astype(int)
    df["played"] = df["played"].astype(int)
    df["won"] = df["won"].astype(int)
    df["drawn"] = df["drawn"].astype(int)
    df["lost"] = df["lost"].astype(int)
    df["gf"] = df["gf"].astype(int)
    df["ga"] = df["ga"].astype(int)
    df["gd"] = df["gd"].astype(int)
    df["points"] = df["points"].astype(int)
    return df


def get_standings_df():
    global _STANDINGS_DF
    if _STANDINGS_DF is None:
        _STANDINGS_DF = load_standings_df()
    return _STANDINGS_DF


def get_all_seasons():
    df = get_standings_df()
    seasons = sorted(df["season_en"].unique().tolist())
    return seasons


def get_table_for_season(season: int, sort_type: str = "points"):
    df = get_standings_df()
    season_df = df[df["season_en"] == season].copy()

    if season_df.empty:
        return []

    if sort_type == "goals_for":
        season_df = season_df.sort_values(
            by=["gf", "gd", "points"], ascending=[False, False, False]
        )
    elif sort_type == "goals_against":
        season_df = season_df.sort_values(
            by=["ga", "gd", "points"], ascending=[True, False, False]
        )
    elif sort_type == "goal_diff":
        season_df = season_df.sort_values(
            by=["gd", "points"], ascending=[False, False]
        )
    else:
        season_df = season_df.sort_values(
            by=["points", "gd"], ascending=[False, False]
        )

    season_df = season_df.reset_index(drop=True)
    season_df["rank"] = season_df.index + 1

    records = []
    for _, row in season_df.iterrows():
        records.append({
            "season": int(row["season_en"]),
            "rank": int(row["rank"]),
            "team": row["team"],
            "played": int(row["played"]),
            "won": int(row["won"]),
            "drawn": int(row["drawn"]),
            "lost": int(row["lost"]),
            "gf": int(row["gf"]),
            "ga": int(row["ga"]),
            "gd": int(row["gd"]),
            "points": int(row["points"]),
        })
    return records
