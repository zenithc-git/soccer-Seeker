# backend/server.py
from flask import Flask, jsonify, request
from data_loader import get_all_seasons, get_table_for_season

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>欢迎访问 Premier League 数据系统 API</h1>
    <p>可用接口：</p>
    <ul>
        <li><a href="/api/seasons">/api/seasons</a> 查看所有赛季</li>
        <li>/api/standings?season=xxxx 获取赛季积分榜</li>
        <li>/api/standings?season=xxxx&type=goals_for 获取进球榜</li>
        <li>/api/standings?season=xxxx&type=goal_diff 获取净胜球榜</li>
    </ul>
    """

# 测试用：检查服务器是否正常
@app.route("/ping")
def ping():
    return jsonify({"msg": "pong"})


# 返回所有赛季列表
@app.route("/api/seasons", methods=["GET"])
def api_seasons():
    seasons = get_all_seasons()
    return jsonify({"seasons": seasons})


# 返回某个赛季的积分/进球/失球/净胜球排序
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


if __name__ == "__main__":
    # host 设成 0.0.0.0 方便以后远程访问
    app.run(host="0.0.0.0", port=5000, debug=True)