# backend/server.py
import secrets
import os
from pathlib import Path

from flask import Flask, jsonify, request
from flask import send_from_directory
from web import webui

from core.db import SessionLocal
from core.db.models import User, Season, Team, TeamSeasonStats, Player

app = Flask(__name__)

# Matplotlib球队历年数据图片API
import io
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 指定为黑体
matplotlib.rcParams['axes.unicode_minus'] = False    # 负号正常显示
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import send_file
@app.route('/api/team_stats_plot')
def team_stats_plot():
    token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = TOKENS.get(token)
    if not user_id:
        return {'error': 'missing or invalid token'}, 401
    session = SessionLocal()
    try:
        user = session.query(User).get(user_id)
        if not user or user.role not in ("vip_user", "admin"):
            return {'error': 'vip access required'}, 403
        team_name = request.args.get('team_name')
        if not team_name:
            return {'error': 'team_name required'}, 400
        team = session.query(Team).filter_by(name=team_name).first()
        if not team:
            return {'error': 'team not found'}, 404
        stats = (
            session.query(TeamSeasonStats, Season)
            .join(Season, TeamSeasonStats.season_id == Season.id)
            .filter(TeamSeasonStats.team_id == team.id)
            .order_by(Season.end_year.asc())
            .all()
        )
        if not stats:
            return {'error': 'no data'}, 404
        seasons = [season.end_year for _, season in stats]
        ranks = [st.position for st, _ in stats]
        gf = [st.gf for st, _ in stats]
        ga = [st.ga for st, _ in stats]
        gd = [st.gd for st, _ in stats]
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))
        ax1.plot(seasons, ranks, marker='o', color='#1976d2', linewidth=2, label='排名')
        ax1.set_title(f'{team_name} 历年排名')
        ax1.set_xlabel('赛季')
        ax1.set_ylabel('排名')
        ax1.invert_yaxis()
        ax1.grid(True, linestyle='--', alpha=0.5)
        ax2.plot(seasons, gf, marker='o', color='#43a047', label='进球')
        ax2.plot(seasons, ga, marker='o', color='#e53935', label='失球')
        ax2.plot(seasons, gd, marker='o', color='#fbc02d', label='净胜球')
        ax2.set_title(f'{team_name} 历年进球/失球/净胜球')
        ax2.set_xlabel('赛季')
        ax2.set_ylabel('数量')
        ax2.legend()
        ax2.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        return send_file(buf, mimetype='image/png')
    finally:
        session.close()
BASE_DIR = Path(__file__).resolve().parent
AVATAR_DIR = BASE_DIR / "uploads" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)


def get_players_for_team(session, team_id: int):
    """Return serialized players for a team from DB."""
    rows = (
        session.query(Player)
        .filter(Player.team_id == team_id)
        .order_by(Player.position.asc(), Player.shirt_no.asc())
        .all()
    )
    result = []
    for p in rows:
        result.append({
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "shirt_no": p.shirt_no,
            "birth_date": p.birth_date.isoformat() if p.birth_date else None,
            "position": p.position,
        })
    return result


# Simple in-memory token store: token -> user_id
TOKENS = {}


def get_auth_user(return_session: bool = False):
    """
    Resolve current user from Authorization header.
    Returns None if missing/invalid.
    When return_session=True, returns (user, session) and caller must close.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(None, 1)[1]
    user_id = TOKENS.get(token)
    if not user_id:
        return None
    session = SessionLocal()
    user = session.query(User).get(user_id)
    if return_session:
        return user, session
    session.close()
    return user


# 新增：球队历年数据API
@app.route("/api/team_stats", methods=["GET"])
def api_team_stats():
    """
    查询参数：team_id 或 team_name（二选一，推荐用 team_id）
    返回该队所有赛季的排名、进球、失球、净胜球数据，按赛季升序排列
    """
    user = get_auth_user()
    if not user:
        return jsonify({"error": "missing or invalid token"}), 401
    if user.role not in ("vip_user", "admin"):
        return jsonify({"error": "vip access required"}), 403

    team_id = request.args.get("team_id", type=int)
    team_name = request.args.get("team_name", type=str)
    if not team_id and not team_name:
        return jsonify({"error": "missing team_id or team_name"}), 400

    session = SessionLocal()
    try:
        if team_id:
            team = session.query(Team).filter_by(id=team_id).first()
        else:
            team = session.query(Team).filter_by(name=team_name).first()
        if not team:
            return jsonify({"error": "team not found"}), 404

        # 查找该队所有赛季的统计
        stats = (
            session.query(TeamSeasonStats, Season)
            .join(Season, TeamSeasonStats.season_id == Season.id)
            .filter(TeamSeasonStats.team_id == team.id)
            .order_by(Season.end_year.asc())
            .all()
        )
        result = []
        for st, season in stats:
            result.append({
                "season": season.end_year,
                "position": st.position,
                "gf": st.gf,
                "ga": st.ga,
                "gd": st.gd
            })
        return jsonify({
            "team": team.name,
            "stats": result
        })
    finally:
        session.close()

@app.route("/")
def home():
    return webui

@app.route("/avatars/<path:filename>")
def serve_avatar(filename):
    """Serve uploaded avatars."""
    return send_from_directory(AVATAR_DIR, filename)


# 上传头像
@app.route("/api/me/avatar", methods=["POST"])
def api_update_avatar():
    auth = get_auth_user(return_session=True)
    if not auth:
        return jsonify({"error": "missing or invalid token"}), 401
    user, session = auth
    try:
        if not user:
            return jsonify({"error": "user not found"}), 404
        if "avatar" not in request.files:
            return jsonify({"error": "missing file field 'avatar'"}), 400
        file = request.files["avatar"]
        if file.filename == "":
            return jsonify({"error": "empty filename"}), 400
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            return jsonify({"error": "unsupported file type"}), 400
        filename = f"{user.id}_{secrets.token_hex(8)}{ext}"
        filepath = AVATAR_DIR / filename
        file.save(filepath)

        # 删除旧头像文件（仅限本目录）
        if user.avatar_url and user.avatar_url.startswith("/avatars/"):
            old_name = user.avatar_url.split("/avatars/", 1)[-1]
            old_path = AVATAR_DIR / old_name
            if old_path.exists():
                try:
                    old_path.unlink()
                except OSError:
                    pass

        user.avatar_url = f"/avatars/{filename}"
        session.commit()
        return jsonify({"msg": "avatar updated", "avatar_url": user.avatar_url})
    finally:
        session.close()


# 修改密码
@app.route("/api/me/password", methods=["POST"])
def api_update_password():
    auth = get_auth_user(return_session=True)
    if not auth:
        return jsonify({"error": "missing or invalid token"}), 401
    user, session = auth
    data = request.json or {}
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    if not old_password or not new_password:
        return jsonify({"error": "old_password and new_password required"}), 400
    if user.password != old_password:
        return jsonify({"error": "old password mismatch"}), 403
    try:
        user.password = new_password
        session.commit()
        return jsonify({"msg": "password updated"})
    finally:
        session.close()

# 测试用：检查服务器是否正常
@app.route("/ping")
def ping():
    return jsonify({"msg": "pong"})

# 返回所有赛季列表
@app.route("/api/seasons", methods=["GET"])
def api_seasons():
    session = SessionLocal()
    try:
        years = [s.end_year for s in session.query(Season).order_by(Season.end_year.asc()).all()]
        return jsonify({"seasons": years})
    finally:
        session.close()
    
@app.route("/api/standings", methods=["GET"])
def api_standings():
    """
    请求参数：
      - season (必需): 例如 2010（这里指 end_year）
      - type   (可选): points / goals_for / goals_against / goal_diff
    """
    season_year = request.args.get("season", type=int)
    sort_type = request.args.get("type", default="points", type=str)

    if season_year is None:
        return jsonify({"error": "missing season"}), 400

    session = SessionLocal()
    try:
        season = session.query(Season).filter_by(end_year=season_year).first()
        if not season:
            return jsonify({"error": f"season {season_year} not found"}), 404

        # 关联 team_season_stats + teams
        q = (
            session.query(TeamSeasonStats, Team)
            .join(Team, Team.id == TeamSeasonStats.team_id)
            .filter(TeamSeasonStats.season_id == season.id)
        )

        # 排序
        if sort_type == "points":
            q = q.order_by(
                TeamSeasonStats.points.desc(),
                TeamSeasonStats.gd.desc(),
                TeamSeasonStats.gf.desc(),
                Team.name.asc(),
            )
        elif sort_type == "goals_for":
            q = q.order_by(
                TeamSeasonStats.gf.desc(),
                TeamSeasonStats.points.desc(),
                Team.name.asc(),
            )
        elif sort_type == "goals_against":
            q = q.order_by(
                TeamSeasonStats.ga.asc(),
                TeamSeasonStats.points.desc(),
                Team.name.asc(),
            )
        elif sort_type == "goal_diff":
            q = q.order_by(
                TeamSeasonStats.gd.desc(),
                TeamSeasonStats.points.desc(),
                Team.name.asc(),
            )
        else:
            return jsonify({"error": f"invalid type: {sort_type}"}), 400

        rows = []
        for st, team in q.all():
            rows.append({
                "team_id": team.id,
                "team": team.name,
                "position": st.position,
                "played": st.played,
                "won": st.won,
                "drawn": st.drawn,
                "lost": st.lost,
                "gf": st.gf,
                "ga": st.ga,
                "gd": st.gd,
                "points": st.points,
            })

        return jsonify({
            "season": season_year,
            "type": sort_type,
            "count": len(rows),
            "rows": rows,
        })
    finally:
        session.close()


@app.route("/api/team_profile", methods=["GET"])
def api_team_profile():
    """
    Team homepage info:
    - Query params: team_id (preferred) or team_name, optional season (end_year).
    - Returns W/D/L for the season and all players of the team.
    """
    team_id = request.args.get("team_id", type=int)
    team_name = request.args.get("team_name", type=str)
    season_year = request.args.get("season", type=int)

    if not team_id and not team_name:
        return jsonify({"error": "missing team_id or team_name"}), 400

    session = SessionLocal()
    try:
        team = session.query(Team).filter_by(id=team_id).first() if team_id else session.query(Team).filter_by(name=team_name).first()
        if not team:
            return jsonify({"error": "team not found"}), 404

        stats_row = None
        season = None
        if season_year:
            season = session.query(Season).filter_by(end_year=season_year).first()
        else:
            season = session.query(Season).order_by(Season.end_year.desc()).first()

        if season:
            stats_row = (
                session.query(TeamSeasonStats)
                .filter_by(team_id=team.id, season_id=season.id)
                .first()
            )

        players = get_players_for_team(session, team.id)

        if not stats_row and not players:
            # Provide a friendly message when no data is available at all
            return jsonify({"error": "no data found for this team"}), 404

        payload = {
            "team_id": team.id,
            "team": team.name,
            "season": season.end_year if season else None,
            "players": players,
            "player_count": len(players),
        }
        if stats_row:
            payload.update({
                "played": stats_row.played,
                "won": stats_row.won,
                "drawn": stats_row.drawn,
                "lost": stats_row.lost,
                "gf": stats_row.gf,
                "ga": stats_row.ga,
                "gd": stats_row.gd,
                "points": stats_row.points,
                "position": stats_row.position,
            })

        return jsonify(payload)
    finally:
        session.close()


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    birthday = data.get("birthday")  # 格式：YYYY-MM-DD
    role = data.get("role")  # 默认角色为"user"

    if not (name and email and password):
        return jsonify({"error": "missing required fields (name,email,password)"}), 400

    session = SessionLocal()
    try:
        # check existing email
        existing = session.query(User).filter_by(email=email).first()
        if existing:
            return jsonify({"error": "email already registered"}), 409

        # create user
        user = User(name=name, email=email, password=password, role=role)
        if birthday:
            from datetime import datetime
            try:
                user.birthday = datetime.strptime(birthday, "%Y-%m-%d").date()
            except Exception:
                pass

        session.add(user)
        session.commit()
        session.refresh(user)

        return jsonify({
            "msg": "注册成功",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "avatar_url": user.avatar_url,
            }
        }), 201
    finally:
        session.close()


@app.route("/api/users", methods=["GET"])
def api_users():
    """返回已注册用户列表（不包含密码）。可用查询参数：role（可选）"""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(None, 1)[1]
    else:
        token = None

    if not token or token not in TOKENS:
        return jsonify({"error": "missing or invalid token"}), 401

    user_id = TOKENS[token]
    session = SessionLocal()

    user = session.query(User).get(user_id)
    if not user or user.role != "admin":
        return jsonify({"error": "admin access required"}), 403

    role = request.args.get("role")
    session = SessionLocal()
    try:
        query = session.query(User)
        if role:
            query = query.filter_by(role=role)

        users = query.all()
        result = []
        for u in users:
            result.append({
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "birthday": u.birthday.isoformat() if getattr(u, "birthday", None) else None,
            })

        return jsonify({"count": len(result), "users": result})
    finally:
        session.close()


@app.route("/api/login", methods=["POST"])
def api_login():
    """Authenticate user and return a simple token."""
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    if not (email and password):
        return jsonify({"error": "missing email or password"}), 400

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(email=email).first()
        if not user or user.password != password:
            return jsonify({"error": "invalid credentials"}), 401

        # create token
        token = secrets.token_hex(16)
        TOKENS[token] = user.id

        return jsonify({
            "msg": "login successful",
            "token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "avatar_url": user.avatar_url,
            }
        })
    finally:
        session.close()


@app.route("/api/me", methods=["GET"])
def api_me():
    """Return current user by Bearer token in Authorization header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(None, 1)[1]
    else:
        token = None

    if not token or token not in TOKENS:
        return jsonify({"error": "missing or invalid token"}), 401

    user_id = TOKENS[token]
    session = SessionLocal()
    try:
        user = session.query(User).get(user_id)
        if not user:
            return jsonify({"error": "user not found"}), 404
        return jsonify({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "avatar_url": user.avatar_url,
        })
    finally:
        session.close()

@app.route("/api/users/me", methods=["DELETE"])
def api_delete_me():
    """Authenticated user deletes their own account. Requires Authorization: Bearer <token>."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(None, 1)[1]
    else:
        token = None

    if not token or token not in TOKENS:
        return jsonify({"error": "missing or invalid token"}), 401

    user_id = TOKENS[token]
    session = SessionLocal()
    try:
        user = session.query(User).get(user_id)
        if not user:
            return jsonify({"error": "user not found"}), 404

        session.delete(user)
        session.commit()

        # remove any tokens that map to this user
        remove = [t for t, uid in list(TOKENS.items()) if uid == user_id]
        for t in remove:
            TOKENS.pop(t, None)

        return jsonify({"msg": "account deleted", "id": user_id})
    finally:
        session.close()


if __name__ == "__main__":
    # host 设成 0.0.0.0 方便以后远程访问
    app.run(host="0.0.0.0", port=5000, debug=True)
