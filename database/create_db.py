from sqlalchemy import (
    create_engine, Column, Integer, String, Date, DateTime, 
    ForeignKey, CheckConstraint, Boolean, UniqueConstraint
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.event import listen
import datetime 

# ------------------------------
# 初始化配置（2.0兼容+外键启用）
# ------------------------------
engine = create_engine(
    'sqlite:///soccer-seeker.db',
    connect_args={"check_same_thread": False}
)

# 启用SQLite外键约束
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
listen(engine, 'connect', set_sqlite_pragma)

Base = declarative_base()  # 2.0无警告
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ------------------------------
# 模型定义（核心：反向关系用「子模型.字段名」字符串指定foreign_keys）
# ------------------------------

# 1. 无依赖基础模型
class Season(Base):
    __tablename__ = 'seasons'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    
    # 反向关系：明确子模型字段
    matches = relationship("Match", foreign_keys="Match.season_id", back_populates="season", cascade="all, delete-orphan")
    team_stats = relationship("TeamSeasonStats", foreign_keys="TeamSeasonStats.season_id", back_populates="season", cascade="all, delete-orphan")

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    
    # 反向关系：明确子模型字段
    users = relationship("User", foreign_keys="User.role_id", back_populates="role", cascade="all, delete-orphan")

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    short_name = Column(String, index=True)
    
    # 反向关系明确子模型的外键字段
    home_matches = relationship(
        "Match", 
        foreign_keys="Match.home_team_id",  # 子模型Match的home_team_id字段
        back_populates="home_team", 
        cascade="all, delete-orphan"
    )
    away_matches = relationship(
        "Match", 
        foreign_keys="Match.away_team_id",  # 子模型Match的away_team_id字段
        back_populates="away_team", 
        cascade="all, delete-orphan"
    )
    team_stats = relationship("TeamSeasonStats", foreign_keys="TeamSeasonStats.team_id", back_populates="team", cascade="all, delete-orphan")
    lineups = relationship("MatchLineup", foreign_keys="MatchLineup.team_id", back_populates="team", cascade="all, delete-orphan")
    goals = relationship("GoalRecord", foreign_keys="GoalRecord.team_id", back_populates="team", cascade="all, delete-orphan")
    player_stats = relationship("PlayerClubStats", foreign_keys="PlayerClubStats.team_id", back_populates="team", cascade="all, delete-orphan")

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False, index=True)
    nationality = Column(String, index=True)
    birth_date = Column(Date)
    version = Column(Integer, default=0)
    
    # 核心修正：反向关系明确子模型的外键字段（GoalRecord.player_id / GoalRecord.assist_player_id）
    goals_scored = relationship(
        "GoalRecord", 
        foreign_keys="GoalRecord.player_id",  # 子模型GoalRecord的player_id字段
        back_populates="scorer", 
        cascade="all, delete-orphan"
    )
    assists = relationship(
        "GoalRecord", 
        foreign_keys="GoalRecord.assist_player_id",  # 子模型GoalRecord的assist_player_id字段
        back_populates="assister", 
        cascade="all, delete-orphan"
    )
    club_stats = relationship("PlayerClubStats", foreign_keys="PlayerClubStats.player_id", back_populates="player", cascade="all, delete-orphan")
    market_values = relationship("PlayerMarketValue", foreign_keys="PlayerMarketValue.player_id", back_populates="player", cascade="all, delete-orphan")
    lineups = relationship("MatchLineup", foreign_keys="MatchLineup.player_id", back_populates="player", cascade="all, delete-orphan")

# 2. 依赖基础模型的关联模型
class Match(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True)
    season_id = Column(Integer, ForeignKey('seasons.id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    home_team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    away_team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    referee = Column(String)
    
    # 全场/半场结果
    ft_home_goals = Column(Integer)
    ft_away_goals = Column(Integer)
    ft_result = Column(String(1), CheckConstraint("ft_result IN ('H', 'A', 'D')"))
    ht_home_goals = Column(Integer)
    ht_away_goals = Column(Integer)
    ht_result = Column(String(1), CheckConstraint("ht_result IN ('H', 'A', 'D')"))
    
    # 技战术统计
    home_shots = Column(Integer)
    away_shots = Column(Integer)
    home_shots_on_target = Column(Integer)
    away_shots_on_target = Column(Integer)
    home_fouls = Column(Integer)
    away_fouls = Column(Integer)
    home_corners = Column(Integer)
    away_corners = Column(Integer)
    home_yellow_cards = Column(Integer)
    away_yellow_cards = Column(Integer)
    home_red_cards = Column(Integer)
    away_red_cards = Column(Integer)
    
    version = Column(Integer, default=0)
    
    # 正向关系：用字段对象指定foreign_keys（模型已定义）
    season = relationship("Season", foreign_keys=season_id, back_populates="matches")
    home_team = relationship("Team", foreign_keys=home_team_id, back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=away_team_id, back_populates="away_matches")
    lineups = relationship("MatchLineup", foreign_keys="MatchLineup.match_id", back_populates="match", cascade="all, delete-orphan")
    goals = relationship("GoalRecord", foreign_keys="GoalRecord.match_id", back_populates="match", cascade="all, delete-orphan")
    
    # 约束：主客场不同
    __table_args__ = (
        CheckConstraint("home_team_id != away_team_id", name="check_different_teams"),
    )

class PlayerClubStats(Base):
    __tablename__ = 'player_club_stats'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False, index=True)
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)
    appearances = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    
    # 正向关系
    player = relationship("Player", foreign_keys=[player_id], back_populates="club_stats")
    team = relationship("Team", foreign_keys=[team_id], back_populates="player_stats")
    
    # 约束：年份顺序+唯一记录
    __table_args__ = (
        CheckConstraint("start_year <= end_year", name="check_year_order"),
        UniqueConstraint('player_id', 'team_id', 'start_year', name='unique_player_team_period'),
    )

class PlayerMarketValue(Base):
    __tablename__ = 'player_market_values'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    market_value_eur = Column(Integer)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=True, index=True)
    note = Column(String)
    
    # 正向关系
    player = relationship("Player", foreign_keys=[player_id], back_populates="market_values")
    team = relationship("Team", foreign_keys=[team_id])

# 3. 依赖关联模型的扩展模型
class TeamSeasonStats(Base):
    __tablename__ = 'team_season_stats'
    id = Column(Integer, primary_key=True)
    season_id = Column(Integer, ForeignKey('seasons.id'), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False, index=True)
    
    mp = Column(Integer, nullable=False, default=0)
    w = Column(Integer, nullable=False, default=0)
    d = Column(Integer, nullable=False, default=0)
    l = Column(Integer, nullable=False, default=0)
    gf = Column(Integer, nullable=False, default=0)
    ga = Column(Integer, nullable=False, default=0)
    gd = Column(Integer, nullable=False, default=0)
    pts = Column(Integer, nullable=False, default=0)
    version = Column(Integer, default=0)
    
    # 正向关系
    season = relationship("Season", foreign_keys=[season_id], back_populates="team_stats")
    team = relationship("Team", foreign_keys=[team_id], back_populates="team_stats")
    
    __table_args__ = (
        UniqueConstraint('season_id', 'team_id', name='unique_team_season'),
    )

class MatchLineup(Base):
    __tablename__ = 'match_lineups'
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False, index=True)
    
    position = Column(String)
    is_start = Column(Boolean, nullable=False, default=True)
    sub_time = Column(Integer)
    shirt_number = Column(Integer)
    
    # 正向关系
    match = relationship("Match", foreign_keys=[match_id], back_populates="lineups")
    team = relationship("Team", foreign_keys=[team_id], back_populates="lineups")
    player = relationship("Player", foreign_keys=[player_id], back_populates="lineups")
    
    __table_args__ = (
        UniqueConstraint('match_id', 'player_id', name='unique_player_match'),
    )

class GoalRecord(Base):
    __tablename__ = 'goal_records'
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False, index=True)
    goal_time = Column(Integer, nullable=False)
    is_penalty = Column(Boolean, default=False)
    is_own_goal = Column(Boolean, default=False)
    assist_player_id = Column(Integer, ForeignKey('players.id'), nullable=True)
    
    # 正向关系
    match = relationship("Match", foreign_keys=[match_id], back_populates="goals")
    team = relationship("Team", foreign_keys=[team_id], back_populates="goals")
    scorer = relationship("Player", foreign_keys=[player_id], back_populates="goals_scored")
    assister = relationship("Player", foreign_keys=[assist_player_id], back_populates="assists")
    
    __table_args__ = (
        CheckConstraint("goal_time >= 0", name="check_goal_time_positive"),
    )

# 4. 用户相关模型
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 正向关系
    role = relationship("Role", foreign_keys=[role_id], back_populates="users")
    login_logs = relationship("LoginLog", foreign_keys="LoginLog.user_id", back_populates="user", cascade="all, delete-orphan")
    browse_logs = relationship("BrowseLog", foreign_keys="BrowseLog.user_id", back_populates="user", cascade="all, delete-orphan")

class LoginLog(Base):
    __tablename__ = 'login_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    login_time = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    ip_address = Column(String)
    
    # 正向关系
    user = relationship("User", foreign_keys=[user_id], back_populates="login_logs")

class BrowseLog(Base):
    __tablename__ = 'browse_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    entity_type = Column(String, CheckConstraint("entity_type IN ('match', 'player', 'team')"), nullable=False)
    entity_id = Column(Integer, nullable=False)
    viewed_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    # 正向关系
    user = relationship("User", foreign_keys=[user_id], back_populates="browse_logs")

# ------------------------------
# 数据库初始化
# ------------------------------
def init_db():
    print("=== 开始初始化数据库 ===")
    try:
        print("正在创建所有数据表...")
        Base.metadata.create_all(bind=engine)
        print("✅ 数据表创建成功（或已存在）")
    except Exception as e:
        print(f"❌ 创建数据表失败：{str(e)}")
        return
    
    # 初始化角色（user/admin）
    db = SessionLocal()
    try:
        print("正在初始化角色数据...")
        required_roles = ['user', 'admin']
        for role_name in required_roles:
            if not db.query(Role).filter_by(name=role_name).first():
                db.add(Role(name=role_name))
        db.commit()
        print("✅ 角色数据初始化成功")
    except Exception as e:
        db.rollback()
        print(f"❌ 初始化角色失败：{str(e)}")
    finally:
        db.close()
        print("=== 数据库初始化流程结束 ===")

if __name__ == "__main__":
    init_db()
    print("🎉 数据库创建完成！可在当前目录查看 soccer-seeker.db 文件")