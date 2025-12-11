from sqlalchemy import func, desc, asc
from datetime import datetime
from create_db import (
    SessionLocal, Season, Team, Match, Player, PlayerClubStats,
    PlayerMarketValue, TeamSeasonStats, MatchLineup, GoalRecord,
    LoginLog, BrowseLog, User
)

# ------------------------------
# 通用工具函数：获取数据库会话
# ------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------
# 联赛积分榜查询
# 功能：按赛季查询积分榜，支持排序（积分/净胜球/进球）和筛选
# 参数：season_id（赛季ID）、sort_by（排序字段）、ascending（是否升序）
# ------------------------------
def query_standings(season_id: int, sort_by: str = "pts", ascending: bool = False):
    db = next(get_db())
    try:
        # 验证排序字段合法性
        valid_sort_fields = ["pts", "gd", "gf", "ga", "mp", "w", "d", "l"]
        if sort_by not in valid_sort_fields:
            sort_by = "pts"  # 默认按积分排序
        
        # 构建查询：关联球队信息，获取完整积分榜
        query = db.query(
            TeamSeasonStats,
            Team.name.label("team_name"),
            Team.short_name.label("team_short_name")
        ).join(
            Team, TeamSeasonStats.team_id == Team.id
        ).filter(
            TeamSeasonStats.season_id == season_id
        )
        
        # 排序逻辑
        sort_func = asc if ascending else desc
        if sort_by == "pts":
            query = query.order_by(sort_func(TeamSeasonStats.pts), sort_func(TeamSeasonStats.gd))
        elif sort_by == "gd":
            query = query.order_by(sort_func(TeamSeasonStats.gd), sort_func(TeamSeasonStats.pts))
        else:
            query = query.order_by(sort_func(getattr(TeamSeasonStats, sort_by)))
        
        # 转换为结构化数据
        results = query.all()
        standings = []
        for stats, team_name, team_short_name in results:
            standings.append({
                "team_id": stats.team_id,
                "team_name": team_name,
                "team_short_name": team_short_name,
                "mp": stats.mp,
                "w": stats.w,
                "d": stats.d,
                "l": stats.l,
                "gf": stats.gf,
                "ga": stats.ga,
                "gd": stats.gd,
                "pts": stats.pts,
                "rank": len(standings) + 1  # 计算排名
            })
        return standings
    except Exception as e:
        print(f"积分榜查询失败：{e}")
        return []

# ------------------------------
# 球队赛季详情查询
# 功能：查询某球队某赛季的所有比赛，含赛季统计
# 参数：team_id（球队ID）、season_id（赛季ID）
# ------------------------------
def query_team_season_detail(team_id: int, season_id: int):
    db = next(get_db())
    try:
        # 1. 查询球队赛季统计（积分、进球等）
        team_stats = db.query(
            TeamSeasonStats,
            Team.name.label("team_name"),
            Season.name.label("season_name")
        ).join(Team).join(Season).filter(
            TeamSeasonStats.team_id == team_id,
            TeamSeasonStats.season_id == season_id
        ).first()
        
        # 2. 查询该赛季所有比赛（主客场合并）
        matches = db.query(
            Match,
            Team.name.label("home_team_name"),
            Team.short_name.label("home_team_short"),
            Team2.name.label("away_team_name"),
            Team2.short_name.label("away_team_short")
        ).join(
            Team, Match.home_team_id == Team.id, isouter=True
        ).join(
            Team2, Match.away_team_id == Team2.id, isouter=True
        ).filter(
            Match.season_id == season_id,
            (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
        ).order_by(Match.date).all()
        
        # 格式化比赛数据
        match_list = []
        for match, home_name, home_short, away_name, away_short in matches:
            # 判断当前球队是主队还是客队
            is_home = match.home_team_id == team_id
            team_goals = match.ft_home_goals if is_home else match.ft_away_goals
            opp_goals = match.ft_away_goals if is_home else match.ft_home_goals
            result = "胜" if (is_home and match.ft_result == "H") or (not is_home and match.ft_result == "A") else \
                     "平" if match.ft_result == "D" else "负"
            
            match_list.append({
                "match_id": match.id,
                "date": match.date.strftime("%Y-%m-%d") if match.date else None,
                "home_team": {
                    "id": match.home_team_id,
                    "name": home_name,
                    "short_name": home_short
                },
                "away_team": {
                    "id": match.away_team_id,
                    "name": away_name,
                    "short_name": away_short
                },
                "result": result,
                "team_goals": team_goals,
                "opponent_goals": opp_goals,
                "referee": match.referee,
                "ht_result": match.ht_result,
                "ht_team_goals": match.ht_home_goals if is_home else match.ht_away_goals,
                "ht_opp_goals": match.ht_away_goals if is_home else match.ht_home_goals
            })
        
        # 格式化赛季统计
        season_detail = {
            "team_id": team_id,
            "team_name": team_stats.team_name if team_stats else None,
            "season_id": season_id,
            "season_name": team_stats.season_name if team_stats else None,
            "stats": {
                "mp": team_stats[0].mp if team_stats else 0,
                "w": team_stats[0].w if team_stats else 0,
                "d": team_stats[0].d if team_stats else 0,
                "l": team_stats[0].l if team_stats else 0,
                "gf": team_stats[0].gf if team_stats else 0,
                "ga": team_stats[0].ga if team_stats else 0,
                "gd": team_stats[0].gd if team_stats else 0,
                "pts": team_stats[0].pts if team_stats else 0
            },
            "matches": match_list
        }
        return season_detail
    except Exception as e:
        print(f"球队赛季详情查询失败：{e}")
        return {}

# ------------------------------
# 3. 比赛详情查询（核心+选做功能）
# 功能：查询比赛完整信息，含技战术统计、双方阵容、进球记录
# 参数：match_id（比赛ID）
# ------------------------------
def query_match_detail(match_id: int):
    db = next(get_db())
    try:
        # 1. 查询比赛基础信息和技战术统计
        match = db.query(
            Match,
            Season.name.label("season_name"),
            HomeTeam.name.label("home_team_name"),
            HomeTeam.short_name.label("home_team_short"),
            AwayTeam.name.label("away_team_name"),
            AwayTeam.short_name.label("away_team_short")
        ).join(Season).join(
            Team, Match.home_team_id == Team.id, isouter=True
        ).join(
            Team2, Match.away_team_id == Team2.id, isouter=True
        ).filter(Match.id == match_id).first()
        
        if not match:
            return {"error": "比赛不存在"}
        
        match_obj, season_name, home_name, home_short, away_name, away_short = match
        
        # 2. 查询双方阵容（首发+替补）
        lineups = db.query(
            MatchLineup,
            Player.full_name.label("player_name"),
            Team.name.label("team_name")
        ).join(Player).join(Team).filter(
            MatchLineup.match_id == match_id
        ).order_by(
            MatchLineup.team_id,
            MatchLineup.is_start.desc(),  # 首发在前
            MatchLineup.position
        ).all()
        
        # 格式化阵容数据
        home_lineup = []
        away_lineup = []
        for lineup, player_name, team_name in lineups:
            lineup_info = {
                "player_id": lineup.player_id,
                "player_name": player_name,
                "position": lineup.position,
                "is_start": lineup.is_start,
                "sub_time": lineup.sub_time,
                "shirt_number": lineup.shirt_number
            }
            if lineup.team_id == match_obj.home_team_id:
                home_lineup.append(lineup_info)
            else:
                away_lineup.append(lineup_info)
        
        # 3. 查询进球记录
        goals = db.query(
            GoalRecord,
            Player.full_name.label("scorer_name"),
            Team.name.label("team_name"),
            AssistPlayer.full_name.label("assister_name")
        ).join(Player, GoalRecord.player_id == Player.id).join(
            Team, GoalRecord.team_id == Team.id
        ).outerjoin(
            Player2, GoalRecord.assist_player_id == Player2.id
        ).filter(
            GoalRecord.match_id == match_id
        ).order_by(GoalRecord.goal_time).all()
        
        goal_list = []
        for goal, scorer_name, team_name, assister_name in goals:
            goal_list.append({
                "goal_time": goal.goal_time,
                "team_name": team_name,
                "scorer": {
                    "id": goal.player_id,
                    "name": scorer_name
                },
                "assister": {
                    "id": goal.assist_player_id,
                    "name": assister_name
                } if assister_name else None,
                "is_penalty": goal.is_penalty,
                "is_own_goal": goal.is_own_goal
            })
        
        # 整合所有数据
        match_detail = {
            "match_id": match_obj.id,
            "season_name": season_name,
            "date": match_obj.date.strftime("%Y-%m-%d") if match_obj.date else None,
            "referee": match_obj.referee,
            "home_team": {
                "id": match_obj.home_team_id,
                "name": home_name,
                "short_name": home_short
            },
            "away_team": {
                "id": match_obj.away_team_id,
                "name": away_name,
                "short_name": away_short
            },
            "full_time": {
                "home_goals": match_obj.ft_home_goals,
                "away_goals": match_obj.ft_away_goals,
                "result": match_obj.ft_result
            },
            "half_time": {
                "home_goals": match_obj.ht_home_goals,
                "away_goals": match_obj.ht_away_goals,
                "result": match_obj.ht_result
            },
            "stats": {
                "home_shots": match_obj.home_shots,
                "away_shots": match_obj.away_shots,
                "home_shots_on_target": match_obj.home_shots_on_target,
                "away_shots_on_target": match_obj.away_shots_on_target,
                "home_fouls": match_obj.home_fouls,
                "away_fouls": match_obj.away_fouls,
                "home_corners": match_obj.home_corners,
                "away_corners": match_obj.away_corners,
                "home_yellow_cards": match_obj.home_yellow_cards,
                "away_yellow_cards": match_obj.away_yellow_cards,
                "home_red_cards": match_obj.home_red_cards,
                "away_red_cards": match_obj.away_red_cards
            },
            "lineups": {
                "home": home_lineup,
                "away": away_lineup
            },
            "goals": goal_list
        }
        return match_detail
    except Exception as e:
        print(f"比赛详情查询失败：{e}")
        return {"error": str(e)}

# ------------------------------
# 4. 球员索引查询（核心功能）
# 功能：按首字母A-Z浏览、模糊搜索球员
# 参数：initial（首字母，可选）、keyword（搜索关键词，可选）、page（页码）、page_size（每页条数）
# ------------------------------
def query_players_index(initial: str = None, keyword: str = None, page: int = 1, page_size: int = 20):
    db = next(get_db())
    try:
        query = db.query(Player)
        
        # 按首字母筛选（忽略大小写）
        if initial and len(initial) == 1:
            initial = initial.upper()
            query = query.filter(Player.full_name.ilike(f"{initial}%"))
        
        # 模糊搜索（支持姓名包含关键词）
        if keyword:
            query = query.filter(Player.full_name.ilike(f"%{keyword}%"))
        
        # 分页处理
        offset = (page - 1) * page_size
        total = query.count()
        players = query.order_by(Player.full_name).offset(offset).limit(page_size).all()
        
        # 格式化数据
        player_list = []
        for player in players:
            player_list.append({
                "player_id": player.id,
                "full_name": player.full_name,
                "nationality": player.nationality,
                "birth_date": player.birth_date.strftime("%Y-%m-%d") if player.birth_date else None
            })
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "players": player_list
        }
    except Exception as e:
        print(f"球员索引查询失败：{e}")
        return {"total": 0, "page": page, "page_size": page_size, "players": []}

# ------------------------------
# 5. 球员详情查询（核心+选做功能）
# 功能：查询球员英超履历、身价趋势、俱乐部表现
# 参数：player_id（球员ID）
# ------------------------------
def query_player_detail(player_id: int):
    db = next(get_db())
    try:
        # 1. 查询球员基础信息
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            return {"error": "球员不存在"}
        
        # 2. 查询英超效力履历（按俱乐部聚合）
        club_stats = db.query(
            PlayerClubStats,
            Team.name.label("team_name"),
            Team.short_name.label("team_short_name")
        ).join(Team).filter(
            PlayerClubStats.player_id == player_id
        ).order_by(PlayerClubStats.start_year).all()
        
        career_list = []
        total_appearances = 0
        total_goals = 0
        for stats, team_name, team_short in club_stats:
            total_appearances += stats.appearances
            total_goals += stats.goals
            career_list.append({
                "team_id": stats.team_id,
                "team_name": team_name,
                "team_short_name": team_short,
                "period": f"{stats.start_year}–{stats.end_year}",
                "appearances": stats.appearances,
                "goals": stats.goals
            })
        
        # 3. 查询身价趋势（时间序列）
        market_values = db.query(
            PlayerMarketValue,
            Team.name.label("team_name")
        ).outerjoin(Team).filter(
            PlayerMarketValue.player_id == player_id
        ).order_by(PlayerMarketValue.date).all()
        
        value_timeline = []
        for value, team_name in market_values:
            value_timeline.append({
                "date": value.date.strftime("%Y-%m-%d") if value.date else None,
                "market_value_eur": value.market_value_eur,
                "team_name": team_name,
                "note": value.note
            })
        
        # 4. 俱乐部表现可视化数据（用于柱状图）
        club_performance = []
        for stats, team_name, _ in club_stats:
            club_performance.append({
                "team_name": team_name,
                "appearances": stats.appearances,
                "goals": stats.goals
            })
        
        # 整合数据
        player_detail = {
            "player_id": player.id,
            "full_name": player.full_name,
            "nationality": player.nationality,
            "birth_date": player.birth_date.strftime("%Y-%m-%d") if player.birth_date else None,
            "total_appearances": total_appearances,
            "total_goals": total_goals,
            "career": career_list,
            "market_value_timeline": value_timeline,
            "club_performance": club_performance
        }
        return player_detail
    except Exception as e:
        print(f"球员详情查询失败：{e}")
        return {"error": str(e)}

# ------------------------------
# 6. 用户行为记录查询（核心功能）
# 功能：查询用户登录日志、浏览历史
# 参数：user_id（用户ID）、limit（浏览历史条数限制）
# ------------------------------
def query_user_behavior(user_id: int, browse_limit: int = 50):
    db = next(get_db())
    try:
        # 1. 查询登录日志（按时间倒序）
        login_logs = db.query(LoginLog).filter(
            LoginLog.user_id == user_id
        ).order_by(desc(LoginLog.login_time)).all()
        
        formatted_logs = []
        for log in login_logs:
            formatted_logs.append({
                "login_id": log.id,
                "login_time": log.login_time.strftime("%Y-%m-%d %H:%M:%S") if log.login_time else None,
                "ip_address": log.ip_address
            })
        
        # 2. 查询浏览历史（最近N条，按时间倒序）
        browse_logs = db.query(
            BrowseLog,
            Match.id.label("match_id"),
            Match.date.label("match_date"),
            HomeTeam.name.label("home_team_name"),
            AwayTeam.name.label("away_team_name"),
            Player.id.label("player_id"),
            Player.full_name.label("player_name")
        ).outerjoin(
            Match,
            (BrowseLog.entity_type == "match") & (BrowseLog.entity_id == Match.id)
        ).outerjoin(
            Team, Match.home_team_id == Team.id, isouter=True
        ).outerjoin(
            Team2, Match.away_team_id == Team2.id, isouter=True
        ).outerjoin(
            Player,
            (BrowseLog.entity_type == "player") & (BrowseLog.entity_id == Player.id)
        ).filter(
            BrowseLog.user_id == user_id
        ).order_by(desc(BrowseLog.viewed_at)).limit(browse_limit).all()
        
        formatted_browses = []
        for log, match_id, match_date, home_name, away_name, player_id, player_name in browse_logs:
            browse_info = {
                "browse_id": log.id,
                "viewed_at": log.viewed_at.strftime("%Y-%m-%d %H:%M:%S") if log.viewed_at else None,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id
            }
            
            # 补充比赛/球员详情
            if log.entity_type == "match" and match_id:
                browse_info["entity_detail"] = {
                    "match_date": match_date.strftime("%Y-%m-%d") if match_date else None,
                    "match_name": f"{home_name} vs {away_name}"
                }
            elif log.entity_type == "player" and player_id:
                browse_info["entity_detail"] = {
                    "player_name": player_name
                }
            
            formatted_browses.append(browse_info)
        
        return {
            "user_id": user_id,
            "login_logs": formatted_logs,
            "browse_history": formatted_browses
        }
    except Exception as e:
        print(f"用户行为记录查询失败：{e}")
        return {"user_id": user_id, "login_logs": [], "browse_history": []}

# ------------------------------
# 7. 管理员数据查询（用于编辑功能）
# 功能：查询单条可编辑数据（球队/球员/比赛/身价记录）
# 参数：entity_type（实体类型）、entity_id（实体ID）
# ------------------------------
def query_admin_entity(entity_type: str, entity_id: int):
    db = next(get_db())
    try:
        valid_types = ["team", "player", "match", "market_value"]
        if entity_type not in valid_types:
            return {"error": "无效实体类型"}
        
        # 按实体类型查询
        if entity_type == "team":
            entity = db.query(Team).filter(Team.id == entity_id).first()
            return {
                "id": entity.id,
                "name": entity.name,
                "short_name": entity.short_name,
                "version": entity.version if hasattr(entity, "version") else 0
            } if entity else {"error": "球队不存在"}
        
        elif entity_type == "player":
            entity = db.query(Player).filter(Player.id == entity_id).first()
            return {
                "id": entity.id,
                "full_name": entity.full_name,
                "nationality": entity.nationality,
                "birth_date": entity.birth_date.strftime("%Y-%m-%d") if entity.birth_date else None,
                "version": entity.version
            } if entity else {"error": "球员不存在"}
        
        elif entity_type == "match":
            entity = db.query(Match).filter(Match.id == entity_id).first()
            return {
                "id": entity.id,
                "season_id": entity.season_id,
                "date": entity.date.strftime("%Y-%m-%d") if entity.date else None,
                "home_team_id": entity.home_team_id,
                "away_team_id": entity.away_team_id,
                "referee": entity.referee,
                "ft_home_goals": entity.ft_home_goals,
                "ft_away_goals": entity.ft_away_goals,
                "ft_result": entity.ft_result,
                "ht_home_goals": entity.ht_home_goals,
                "ht_away_goals": entity.ht_away_goals,
                "ht_result": entity.ht_result,
                "version": entity.version
            } if entity else {"error": "比赛不存在"}
        
        elif entity_type == "market_value":
            entity = db.query(PlayerMarketValue).filter(PlayerMarketValue.id == entity_id).first()
            return {
                "id": entity.id,
                "player_id": entity.player_id,
                "date": entity.date.strftime("%Y-%m-%d") if entity.date else None,
                "market_value_eur": entity.market_value_eur,
                "team_id": entity.team_id,
                "note": entity.note
            } if entity else {"error": "身价记录不存在"}
    
    except Exception as e:
        print(f"管理员实体查询失败：{e}")
        return {"error": str(e)}

# ------------------------------
# 测试函数：验证所有查询功能
# ------------------------------
if __name__ == "__main__":
    # 1. 测试积分榜查询（假设赛季ID=1）
    print("="*50)
    print("测试1：积分榜查询（赛季ID=1，按积分降序）")
    standings = query_standings(season_id=1, sort_by="pts")
    print(f"查询到 {len(standings)} 支球队")
    for team in standings[:3]:  # 打印前3名
        print(f"排名{team['rank']}：{team['team_name']} - 积分{team['pts']} 净胜球{team['gd']}")
    
    # 2. 测试球队赛季详情（假设球队ID=1，赛季ID=1）
    print("\n" + "="*50)
    print("测试2：球队赛季详情（球队ID=1，赛季ID=1）")
    team_detail = query_team_season_detail(team_id=1, season_id=1)
    print(f"球队：{team_detail['team_name']} 赛季：{team_detail['season_name']}")
    print(f"赛季统计：{team_detail['stats']}")
    print(f"该赛季比赛数：{len(team_detail['matches'])}")
    
    # 3. 测试比赛详情（假设比赛ID=1）
    print("\n" + "="*50)
    print("测试3：比赛详情（比赛ID=1）")
    match_detail = query_match_detail(match_id=1)
    if "error" not in match_detail:
        print(f"比赛：{match_detail['home_team']['name']} {match_detail['full_time']['home_goals']}-{match_detail['full_time']['away_goals']} {match_detail['away_team']['name']}")
        print(f"进球数：{len(match_detail['goals'])}")
        print(f"主队首发数：{len([l for l in match_detail['lineups']['home'] if l['is_start']])}")
    
    # 4. 测试球员索引（首字母M，模糊搜索"Messi"）
    print("\n" + "="*50)
    print("测试4：球员索引查询（首字母M，关键词Messi）")
    players = query_players_index(initial="M", keyword="Messi")
    print(f"查询到 {players['total']} 名球员")
    for p in players['players']:
        print(f"球员：{p['full_name']} 国籍：{p['nationality']}")
    
    # 5. 测试球员详情（假设球员ID=1）
    print("\n" + "="*50)
    print("测试5：球员详情（球员ID=1）")
    player_detail = query_player_detail(player_id=1)
    if "error" not in player_detail:
        print(f"球员：{player_detail['full_name']} 总出场：{player_detail['total_appearances']} 总进球：{player_detail['total_goals']}")
        print(f"效力俱乐部数：{len(player_detail['career'])}")
        print(f"身价记录数：{len(player_detail['market_value_timeline'])}")
    
    # 6. 测试用户行为记录（假设用户ID=1）
    print("\n" + "="*50)
    print("测试6：用户行为记录（用户ID=1）")
    user_behavior = query_user_behavior(user_id=1)
    print(f"登录次数：{len(user_behavior['login_logs'])}")
    print(f"浏览历史数：{len(user_behavior['browse_history'])}")
    
    # 7. 测试管理员实体查询（查询球员ID=1）
    print("\n" + "="*50)
    print("测试7：管理员球员查询（球员ID=1）")
    admin_entity = query_admin_entity(entity_type="player", entity_id=1)
    if "error" not in admin_entity:
        print(f"球员信息：{admin_entity['full_name']} 国籍：{admin_entity['nationality']}")