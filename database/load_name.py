import pandas as pd
from your_model_file import SessionLocal, Player
import datetime

def import_players_from_csv(csv_path: str):
    db = SessionLocal()
    try:
        # 1. 读取 CSV（指定日期列格式）
        df = pd.read_csv(
            csv_path,
            parse_dates=['birth_date'],  # 自动解析日期列
            date_format='%Y-%m-%d'       # 日期格式：年-月-日
        )
        # 处理可能的空值（替换为 None，适配数据库 NULL）
        df = df.fillna(value={
            'nationality': None,
            'birth_date': None
        })

        # 2. 批量转换为 Player 对象（去重：按 full_name 判断）
        players_to_add = []
        existing_names = db.query(Player.full_name).all()  # 已存在的球员姓名
        existing_names = {name[0] for name in existing_names}  # 转为集合，查询更快

        for _, row in df.iterrows():
            if row['full_name'] not in existing_names:
                player = Player(
                    full_name=row['full_name'],
                    nationality=row['nationality'],
                    birth_date=row['birth_date'].date() if pd.notna(row['birth_date']) else None
                )
                players_to_add.append(player)
                existing_names.add(row['full_name'])  # 避免同一 CSV 内重复

        # 3. 批量提交（add_all 比循环 add 效率高 10-100 倍）
        if players_to_add:
            db.add_all(players_to_add)
            db.commit()
            print(f"成功导入 {len(players_to_add)} 名球员")
        else:
            print("无新球员数据可导入")

    except Exception as e:
        db.rollback()
        print(f"CSV 导入失败：{e}")
    finally:
        db.close()

# 执行导入（替换为你的 CSV 路径）
import_players_from_csv("players.csv")