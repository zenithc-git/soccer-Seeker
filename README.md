## soccer-Seeker 
---

# ⚽ 足球联赛数据查询与分析系统

**Python 课程项目 / 联赛信息管理 + 数据分析 + 可视化**

本系统实现了 **联赛、球队、赛程、积分榜、历史对战、趋势图分析** 等功能，并包含用户权限系统、网络模块、数据库支持、数据爬虫与可视化等内容，全面满足课程实践指导书的要求。

---

# 📌 1. 项目简介

本系统是一个基于 Python 的 **足球联赛数据管理与可视化系统**，支持查询欧洲主流联赛（如英超、西甲）或选定赛季的数据。用户可通过系统查看：

* 球队信息
* 赛程与比分
* 积分榜
* 球队总进球、总失球、净胜球、胜平负
* 历史对战情况
* 趋势图（积分走势、进球走势等）

系统分为两个角色：

* **普通用户（球迷）**：查询信息、查看统计、查看趋势图
* **管理员**：数据维护、爬虫更新、可视化分析窗口

并支持 **远程登录访问**（网络模块：Flask 服务器 + tkinter 客户端）。

---

# 📌 2. 技术栈

* **语言**：Python
* **数据库**：SQLite
* **后端网络**：Flask（REST API）
* **客户端界面**：tkinter
* **可视化**：matplotlib
* **爬虫**：requests + BeautifulSoup
* **依赖管理**：pip / venv

---

# 📌 3. 系统功能列表

## ✅ 基本功能（必做）

* [x] GUI 用户界面（tkinter）
* [x] 用户登录 / 注销
* [x] 用户身份区分（user / admin）
* [x] 数据库支持（SQLite）
* [x] 远程访问（客户端 → Flask 后端）
* [x] 球队信息查询
* [x] 赛程查询（按联赛/日期/球队）
* [x] 积分榜查询
* [x] 球队统计（总进球、总失球、净胜球、胜-平-负）
* [x] 历史对战查询
* [x] 个人信息维护（用户）

## ⭐ 附加功能（可选但已支持）

* [x] 爬虫：自动爬取比赛/积分数据更新数据库
* [x] 可视化分析（matplotlib）：

  * 积分趋势图
  * 进球趋势图
  * 联赛总进球柱状图
* [x] 管理员数据维护模块（增删改查）

---

# 📌 4. 系统架构设计

系统采用典型的 **客户端 - 服务器 - 数据库** 三层架构：

```
GUI (tkinter 客户端)
       ↓
Flask 后端（REST API）
       ↓
SQLite 数据库
```

模块说明：

* GUI：用户登录、查询界面、趋势图展示
* Flask：业务逻辑 + 数据API + 爬虫触发
* SQLite：保存球队、赛程、比赛记录等数据
* Crawler：爬取联赛赛程、比分、积分榜数据
* Analysis：统计与可视化模块

---

# 📌 5. 功能模块设计

## 5.1 用户系统（登录/权限）

### 普通用户

* 查询球队信息
* 查询赛程、积分榜
* 查看球队统计数据
* 查看历史对战记录
* 查看趋势图
* 修改个人信息

### 管理员

* 新增/修改/删除比赛
* 手动更新数据（爬虫）
* 查看可视化分析图表
* 数据统计管理

---

# 📌 6. 数据库设计（表结构）

使用 SQLite，共包含以下核心表：

### `users`

| 字段       | 类型      | 说明               |
| -------- | ------- | ---------------- |
| id       | INTEGER | 主键               |
| username | TEXT    | 用户名              |
| password | TEXT    | 密码               |
| role     | TEXT    | 'user' / 'admin' |
| email    | TEXT    | 可选字段             |

---

### `teams`

| 字段      | 类型      | 说明         |
| ------- | ------- | ---------- |
| id      | INTEGER | 主键         |
| name    | TEXT    | 球队名        |
| league  | TEXT    | 联赛名（英超/西甲） |
| city    | TEXT    | 可选         |
| stadium | TEXT    | 可选         |

---

### `matches`

| 字段           | 类型      | 说明     |
| ------------ | ------- | ------ |
| id           | INTEGER | 主键     |
| league       | TEXT    | 联赛名    |
| season       | TEXT    | 赛季     |
| round        | INTEGER | 轮次（可选） |
| date         | TEXT    | 比赛日期   |
| home_team_id | INTEGER | 主队     |
| away_team_id | INTEGER | 客队     |
| home_goals   | INTEGER | 主队进球   |
| away_goals   | INTEGER | 客队进球   |

---

### （可选）`players`

* 球员信息表（如需显示球员数据）

### （可选）`favorites`

* 用户收藏球队/比赛

---

# 📌 7. 后端 API 设计（Flask）

后端包含以下接口：

## 🔒 登录类

* `/login`
* 返回：是否成功 + 用户角色

## ⚽ 查询类

* `/teams`：获取球队列表
* `/matches`：按条件查询赛程
* `/standings`：积分榜
* `/team_stats`：总进球/总失球/净胜球等
* `/h2h`：历史对战（Head-to-Head）
* `/team_trend`：趋势数据

## 🔧 管理类（管理员权限）

* `/admin/add_match`
* `/admin/update_match`
* `/admin/delete_match`
* `/admin/crawl_update`：爬虫更新数据库

---

# 📌 8. 爬虫模块

位置：`crawler/league_crawler.py`

实现功能：

* 从联赛赛程页面爬取：

  * 日期
  * 主队/客队
  * 比分
* 映射到数据库球队 ID
* 更新 `matches` 表
* 更新积分榜数据
* 后端通过 API `/admin/crawl_update` 触发

使用技术：

```python
requests
BeautifulSoup
sqlite3
```

---

# 📌 9. 数据分析 & 可视化模块

位置：`analysis/stats_and_plots.py`

## 支持的图表：

* 球队积分趋势图
* 球队进球趋势图
* 联赛总进球柱状图
* 球队胜/平/负分布统计图

## 使用技术：

* `matplotlib`
* `FigureCanvasTkAgg` 将图嵌入 tkinter

---

# 📌 10. 客户端 GUI（tkinter）

## 登录界面

* 输入用户名 + 密码
* 登录成功后根据角色进入对应界面

## 普通用户界面

* 查询球队列表
* 查询赛程 & 比分
* 查看积分榜
* 查看球队统计数据
* 查看趋势图
* 历史对战查询

## 管理员界面

* 比赛维护（增删改查）
* 一键爬虫数据更新
* 打开可视化统计窗口

---

# 📌 11. 项目目录结构

```plaintext
football_project/
├─ client/
│   ├─ main_gui.py
│   ├─ user_window.py
│   └─ admin_window.py
│
├─ server/
│   ├─ app.py
│   ├─ db.py
│   └─ models.sql
│
├─ crawler/
│   └─ league_crawler.py
│
├─ analysis/
│   └─ stats_and_plots.py
│
└─ docs/
    ├─ design.md
    └─ requirements.md
```

---

# 📌 12. 测试 checklist

* [ ] 登录/注销正常
* [ ] 用户权限正确区分
* [ ] 球队查询返回正确数据
* [ ] 赛程过滤（按日期/球队）正常
* [ ] 积分榜排序正确
* [ ] 历史对战返回正确胜平负
* [ ] 趋势图能显示
* [ ] 管理员能修改比赛数据
* [ ] 爬虫能更新数据库
* [ ] 客户端能访问远程 Flask（网络模块）

---

# 📌 13. 运行方式

```bash
# 启动后端服务
cd server
python app.py

# 启动客户端
cd client
python main_gui.py
```

---

# 📌 14. PPT 建议内容（验收用）

* 项目背景与目标
* 系统功能模块图
* 数据库 ER 图
* 系统架构图（客户端→Flask→SQLite）
* 核心功能展示：

  * 球队查询
  * 赛程
  * 积分榜
  * 历史对战
  * 趋势图
* 管理员模块展示
* 爬虫更新演示
* 小组分工
* 扩展方向（更多联赛、预测模型、球员分析等）

---

# 📌 15. 后续可扩展方向

* 引入球员数据 & 球员统计
* 使用足球 API 做实时分析
* 加入预测模型（如简单 logistic 回归预测比赛结果）
* 多联赛联动分析
* Web 可视化（Flask + 前端页面）

---

如需，我可以继续帮你补齐：
✔ 数据库建表 SQL
✔ Flask API 骨架代码
✔ tkinter 界面框架
✔ 爬虫 Demo

你要哪个，我就继续帮你写哪个。
