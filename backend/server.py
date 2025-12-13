# backend/server.py
from flask import Flask, jsonify, request
from data_loader import get_all_seasons, get_table_for_season
import secrets
from web import webui

# DB imports for saving users
from core.db import SessionLocal
from core.db.models import User

app = Flask(__name__)

# Simple in-memory token store: token -> user_id
TOKENS = {}

@app.route("/")
def home():
    return webui

# 测试用：检查服务器是否正常
@app.route("/ping")
def ping():
    return jsonify({"msg": "pong"})

# 返回所有赛季列表
@app.route("/api/seasons", methods=["GET"])
def api_seasons():
    seasons = get_all_seasons()
    return jsonify({"seasons": seasons})
    
@app.route("/api/standings", methods=["GET"])
def api_standings():
    """
    请求参数：
      - season (必需): 例如 2010
      - type   (可选): points / goals_for / goals_against / goal_diff
    """
    season = request.args.get("season", type=int)
    sort_type = request.args.get("type", default="points", type=str)

    if season is None:
        return jsonify({"error": "missing season"}), 400

    rows = get_table_for_season(season, sort_type)
    return jsonify({
        "season": season,
        "type": sort_type,
        "count": len(rows),
        "rows": rows,
    })

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

        return jsonify({"msg": "login successful", "token": token, "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}})
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
        return jsonify({"id": user.id, "name": user.name, "email": user.email, "role": user.role})
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

