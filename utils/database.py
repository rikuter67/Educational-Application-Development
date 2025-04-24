import sqlite3
import json
import time
import uuid
import logging
from pathlib import Path

# 定数
DB_PATH = "thinking_app.db"

# データベース初期化
def init_database():
    """SQLiteデータベースを必要なテーブルで初期化"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # ユーザーテーブル
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at FLOAT NOT NULL,
                xp_points INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                streak_days INTEGER DEFAULT 0,
                last_active FLOAT,
                badges TEXT DEFAULT '[]',
                settings TEXT DEFAULT '{"notifications": true, "sound": true, "theme": "light"}',
                learning_paths TEXT DEFAULT '["基礎思考力"]'
            )  
            ''')
            
            # セッションテーブル
            cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at FLOAT NOT NULL,
                updated_at FLOAT NOT NULL,
                category TEXT,
                problem_index INTEGER DEFAULT 0,
                hint_step INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')
            
            # チャット履歴テーブル
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                problem_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL, 
                timestamp FLOAT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
            ''')
            
            # 思考ログテーブル
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS thought_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                problem_id TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp FLOAT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
            ''')
            
            # 問題解答テーブル
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS problem_attempts (
                attempt_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                problem_id TEXT NOT NULL,
                category TEXT NOT NULL,
                timestamp FLOAT NOT NULL,
                duration FLOAT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                hints_used INTEGER DEFAULT 0,
                thought_length INTEGER DEFAULT 0,
                answer_text TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')
            
            # 日次目標テーブル
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                goal_type TEXT NOT NULL,
                target_value INTEGER NOT NULL,
                current_value INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, date, goal_type)
            )
            ''')
            
            return True
    except sqlite3.Error as e:
        logging.error(f"データベース初期化エラー: {str(e)}")
        return False

# ユーザー取得/作成
def get_or_create_user(user_id=None, username=None):
    """既存ユーザーの取得または新規ユーザーの作成"""
    if user_id is None:
        user_id = str(uuid.uuid4())
    
    if username is None:
        username = f"ユーザー{user_id[:6]}"
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # ユーザー存在確認
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                # ユーザーが存在する場合
                columns = [column[0] for column in cursor.description]
                user_dict = {columns[i]: user_data[i] for i in range(len(columns))}
                
                # JSON文字列をPythonオブジェクトに変換
                user_dict["badges"] = json.loads(user_dict["badges"])
                user_dict["settings"] = json.loads(user_dict["settings"])
                user_dict["learning_paths"] = json.loads(user_dict["learning_paths"])
                
                return user_dict
            else:
                # 新規ユーザー作成
                now = time.time()
                new_user = {
                    "user_id": user_id,
                    "username": username,
                    "created_at": now,
                    "xp_points": 0,
                    "level": 0,
                    "streak_days": 0,
                    "last_active": now,
                    "badges": [],
                    "settings": {"notifications": True, "sound": True, "theme": "light"},
                    "learning_paths": ["基礎思考力"]
                }
                
                # データベースに挿入
                cursor.execute(
                    """INSERT INTO users 
                       (user_id, username, created_at, xp_points, level, streak_days,
                        last_active, badges, settings, learning_paths)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        new_user["user_id"],
                        new_user["username"],
                        new_user["created_at"],
                        new_user["xp_points"],
                        new_user["level"],
                        new_user["streak_days"],
                        new_user["last_active"],
                        json.dumps(new_user["badges"]),
                        json.dumps(new_user["settings"]),
                        json.dumps(new_user["learning_paths"])
                    )
                )
                
                return new_user
    except sqlite3.Error as e:
        logging.error(f"ユーザーデータベースエラー: {str(e)}")
        # エラー時の仮ユーザー
        return {
            "user_id": user_id or str(uuid.uuid4()),
            "username": username or "ゲストユーザー",
            "created_at": time.time(),
            "xp_points": 0,
            "level": 0,
            "badges": [],
            "settings": {"notifications": True, "sound": True, "theme": "light"},
            "learning_paths": ["基礎思考力"]
        }

# ユーザープロフィール保存
def save_user_profile(user):
    """ユーザープロフィールをデータベースに保存"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """UPDATE users SET
                   username = ?,
                   xp_points = ?,
                   level = ?,
                   streak_days = ?,
                   last_active = ?,  
                   badges = ?,
                   settings = ?,
                   learning_paths = ?
                   WHERE user_id = ?""",
                (
                    user["username"],
                    user["xp_points"],
                    user["level"],
                    user["streak_days"],
                    user["last_active"],
                    json.dumps(user["badges"]),
                    json.dumps(user["settings"]),
                    json.dumps(user["learning_paths"]),
                    user["user_id"]
                )
            )
            
            return True
    except sqlite3.Error as e:
        logging.error(f"ユーザープロフィール保存エラー: {str(e)}")
        return False

# 問題解答記録の保存
def save_problem_attempt(attempt):
    """問題解答記録をデータベースに保存"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO problem_attempts
                   (attempt_id, user_id, problem_id, category, timestamp,
                    duration, is_correct, hints_used, thought_length, answer_text)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                (
                    attempt["attempt_id"],
                    attempt["user_id"],
                    attempt["problem_id"],
                    attempt["category"],
                    attempt["timestamp"],
                    attempt["duration"],
                    attempt["is_correct"],
                    attempt["hints_used"],
                    attempt["thought_length"],
                    attempt["answer_text"]
                )
            )
            
            return True
    except sqlite3.Error as e:
        logging.error(f"問題解答記録エラー: {str(e)}")
        return False

# セッション保存
def save_session(session_id, user_id, category, problem_idx, hint_step):
    """セッションデータをデータベースに保存"""
    try:
        now = time.time()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # セッション存在確認
            cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
            existing = cursor.fetchone()
            
            if existing:
                # 既存セッション更新
                cursor.execute(
                    """UPDATE sessions SET  
                       updated_at = ?,
                       category = ?,
                       problem_index = ?,
                       hint_step = ?
                       WHERE session_id = ?""",
                    (now, category, problem_idx, hint_step, session_id)
                )
            else:
                # 新規セッション作成
                cursor.execute(
                    """INSERT INTO sessions
                       (session_id, user_id, created_at, updated_at, category, problem_index, hint_step)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                    (session_id, user_id, now, now, category, problem_idx, hint_step)
                )
            
            return True
    except sqlite3.Error as e:
        logging.error(f"セッション保存エラー: {str(e)}")
        return False

# チャットメッセージ保存
def save_chat_messages(session_id, problem_id, messages):
    """チャットメッセージをデータベースに保存"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 既存メッセージ削除
            cursor.execute(
                "DELETE FROM chat_history WHERE session_id = ? AND problem_id = ?",
                (session_id, problem_id)
            )
            
            # 新しいメッセージを挿入
            for msg in messages:
                cursor.execute(
                    """INSERT INTO chat_history
                       (session_id, problem_id, role, content, timestamp)
                       VALUES (?, ?, ?, ?, ?)""",
                    (session_id, problem_id, msg["role"], msg["text"], msg.get("timestamp", time.time()))
                )
            
            return True
    except sqlite3.Error as e:
        logging.error(f"チャット履歴保存エラー: {str(e)}")
        return False

# 思考ログ保存
def save_thought_logs(session_id, problem_id, thoughts):
    """思考ログをデータベースに保存"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # 既存思考ログ削除
            cursor.execute(
                "DELETE FROM thought_logs WHERE session_id = ? AND problem_id = ?",
                (session_id, problem_id)
            )
            
            # 新しい思考ログを挿入
            for i, thought in enumerate(thoughts):
                cursor.execute(
                    """INSERT INTO thought_logs
                       (session_id, problem_id, content, timestamp) 
                       VALUES (?, ?, ?, ?)""",
                    (session_id, problem_id, thought, time.time() - (len(thoughts) - i))
                )
            
            return True
    except sqlite3.Error as e:
        logging.error(f"思考ログ保存エラー: {str(e)}")
        return False

# ユーザー統計の取得
def get_user_stats(user_id):
    """ユーザー統計データをデータベースから取得"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 全体統計
            cursor.execute(
                """SELECT 
                   COUNT(*) as total_attempts,
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers,
                   AVG(CASE WHEN is_correct = 1 THEN duration ELSE NULL END) as avg_correct_time,
                   SUM(hints_used) as total_hints,
                   AVG(thought_length) as avg_thought_length  
                   FROM problem_attempts
                   WHERE user_id = ?""",
                (user_id,)
            )
            
            overall_row = cursor.fetchone()
            overall = dict(overall_row) if overall_row else {
                "total_attempts": 0,
                "correct_answers": 0,
                "avg_correct_time": 0,
                "total_hints": 0,
                "avg_thought_length": 0
            }
            
            # 成功率の計算
            if overall["total_attempts"]:
                overall["success_rate"] = (overall["correct_answers"] / overall["total_attempts"]) * 100
            else:
                overall["success_rate"] = 0
                
            # カテゴリ別分析
            cursor.execute(
                """SELECT 
                   category,
                   COUNT(*) as attempts,
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                   FROM problem_attempts
                   WHERE user_id = ?
                   GROUP BY category""",
                (user_id,)
            )
            
            categories = [dict(row) for row in cursor.fetchall()]
            
            # 最近の活動 - 最新10件
            cursor.execute(
                """SELECT * FROM problem_attempts
                   WHERE user_id = ?
                   ORDER BY timestamp DESC
                   LIMIT 10""",
                (user_id,)
            )
            
            recent = [dict(row) for row in cursor.fetchall()]
            
            # 過去30日の日別活動
            thirty_days_ago = time.time() - (30 * 24 * 60 * 60) 
            cursor.execute(
                """SELECT 
                   date(datetime(timestamp, 'unixepoch', 'localtime')) as day,  
                   COUNT(*) as attempts,
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
                   FROM problem_attempts
                   WHERE user_id = ? AND timestamp >= ?
                   GROUP BY day
                   ORDER BY day""",
                (user_id, thirty_days_ago)
            )
            
            daily = [dict(row) for row in cursor.fetchall()]
            
            return {
                "overall": overall,
                "categories": categories,
                "recent": recent,
                "daily": daily  
            }
    except sqlite3.Error as e:
        logging.error(f"統計データ取得エラー: {str(e)}")
        return {  
            "overall": {
                "total_attempts": 0,
                "correct_answers": 0,
                "avg_correct_time": 0,
                "total_hints": 0,
                "avg_thought_length": 0,
                "success_rate": 0
            },
            "categories": [],
            "recent": [],
            "daily": []
        }