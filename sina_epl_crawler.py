# sina_epl_crawler.py
import os
import json
import csv
import requests

API_URL = "https://api.sports.sina.com.cn/"


def fetch_epl_standings(season=2025, debug_print=False):
    """
    从新浪体育接口获取英超积分榜数据（对应页面：https://sports.sina.com.cn/g/pl/table.html）

    参数:
        season: int, 赛季年份，例如 2025 表示 2025/26 赛季
        debug_print: 是否打印原始 JSON 结构，方便调字段名（调试用）

    返回:
        standings: list[dict]，每个元素是一支球队的数据
    """
    params = {
        "p": "sports",
        "s": "sport_client",
        "a": "index",
        "_sport_t_": "football",
        "_sport_s_": "opta",
        "_sport_a_": "teamOrder",
        "use_type": "group",   # 这里决定 data 是分组 dict
        "type": "4",           # 4 = 英超
        "season": season,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://sports.sina.com.cn/g/pl/table.html",
    }

    resp = requests.get(API_URL, params=params, headers=headers, timeout=10)
    resp.raise_for_status()

    data = resp.json()

    result = data.get("result") or {}
    status = result.get("status") or {}
    if status.get("code") != 0:
        raise RuntimeError(f"API 返回错误: {status}")

    raw_data = result.get("data")

    if debug_print:
        print("=== result.status ===")
        print(status)
        print("=== result.data 类型 ===", type(raw_data))
        # 预览前 2000 字符，防止太长
        print(json.dumps(raw_data, ensure_ascii=False, indent=2)[:2000])

    # ---- 关键：把 data 拍平成 list[dict] ----
    teams_raw = []

    if isinstance(raw_data, list):
        teams_raw = raw_data
    elif isinstance(raw_data, dict):
        # use_type=group 时一般是 {"A":[...], "B":[...], ...}
        for group_key, group_list in raw_data.items():
            if isinstance(group_list, list):
                teams_raw.extend(group_list)
            else:
                print(f"[WARN] 分组 {group_key} 的数据不是 list，而是 {type(group_list)}")
    else:
        print("[ERROR] 未知的 data 结构类型：", type(raw_data))
        return []

    standings = []

    for idx, item in enumerate(teams_raw, start=1):
        if not isinstance(item, dict):
            print(f"[WARN] 第 {idx} 条不是 dict，而是 {type(item)}：{item}")
            continue

        # 下面这些字段名是根据新浪常见结构写的，如果你 debug_print 之后
        # 发现字段名不同，就在这里改。
        team_name = (
            item.get("team_cn")
            or item.get("team_name")
            or item.get("teamName")
            or item.get("team_en")
            or ""
        )

        # 总场次
        played = (
            item.get("count")
            or item.get("matches")
            or item.get("match_num")
        )

        # 胜平负
        win = item.get("win")
        draw = item.get("draw")
        lose = item.get("lose")

        # 进 / 失球
        goals_for = item.get("goal") or item.get("goals_for")
        goals_against = (
            item.get("losegoal")
            or item.get("fumble")
            or item.get("goals_against")
        )

        # 积分
        points = item.get("score") or item.get("points")

        # 净胜球：接口里可能有 truegoal / goal_diff，没有的话我们自己算
        goal_diff = item.get("truegoal")
        if goal_diff is None and goals_for is not None and goals_against is not None:
            try:
                goal_diff = int(goals_for) - int(goals_against)
            except Exception:
                goal_diff = None

        rank = item.get("team_order") or idx

        standings.append(
            {
                "rank": rank,
                "team_name": team_name,
                "played": played,
                "win": win,
                "draw": draw,
                "lose": lose,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "goal_diff": goal_diff,
                "points": points,
            }
        )

    # 再按照 积分 & 净胜球 排序一遍，保险
    def to_int(x):
        try:
            return int(x)
        except Exception:
            return 0

    standings.sort(
        key=lambda row: (-to_int(row["points"]), -to_int(row["goal_diff"] or 0))
    )

    # 排序后重新编号 rank
    for i, row in enumerate(standings, start=1):
        row["rank"] = i

    return standings


def save_standings_to_files(standings, season, out_dir="data"):
    """
    把积分榜数据保存到 JSON 和 CSV 文件。

    文件名示例：
        data/epl_standings_2025.json
        data/epl_standings_2025.csv
    """
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, f"epl_standings_{season}.json")
    csv_path = os.path.join(out_dir, f"epl_standings_{season}.csv")

    # ---- 保存 JSON ----
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(standings, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 已保存 JSON：{json_path}")

    # ---- 保存 CSV ----
    if standings:
        fieldnames = list(standings[0].keys())
    else:
        fieldnames = [
            "rank",
            "team_name",
            "played",
            "win",
            "draw",
            "lose",
            "goals_for",
            "goals_against",
            "goal_diff",
            "points",
        ]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in standings:
            writer.writerow(row)

    print(f"[INFO] 已保存 CSV：{csv_path}")


if __name__ == "__main__":
    # 你可以改成 2024 / 2023 等对应不同赛季
    season = 2025

    # 第一次调试可以把 debug_print=True 看一下字段结构
    standings = fetch_epl_standings(season=season, debug_print=False)

    # 控制台简单打印前几条，确认一下
    for row in standings[:5]:
        print(
            f"{row['rank']:>2}. {row['team_name']:<20} "
            f"{row['played']}场 {row['win']}胜 {row['draw']}平 {row['lose']}负  "
            f"进{row['goals_for']} 失{row['goals_against']} 净{row['goal_diff']}  "
            f"积{row['points']}"
        )

    # 关键：落盘保存
    save_standings_to_files(standings, season=season, out_dir="data")
