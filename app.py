import streamlit as st
import json
import uuid
import time
import logging
import sqlite3
from pathlib import Path
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie

# アプリ設定を最初に行う（他のStreamlitコマンドより前）
st.set_page_config(
    page_title="思考力マスター",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 定数
APP_NAME = "思考力マスター"
APP_VERSION = "1.0.1"
THEME_COLOR = "#4F8BF9"
DB_PATH = "thinking_app.db"
PROBLEM_JSON = "problems.json"

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)

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
        st.error(f"データベース初期化エラー: {str(e)}")
        return False

# セッション状態の初期化
def init_session_state():
    """セッション状態を初期化する関数"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.start_time = time.time()
        st.session_state.problem_index = 0
        st.session_state.hint_step = 0
        st.session_state.current_category = None
        st.session_state.chat_history = []
        st.session_state.thought_logs = []
        st.session_state.answer_submitted = False
        
        # ユーザー取得/作成
        try:
            st.session_state.user = get_or_create_user()
        except Exception as e:
            logging.error(f"ユーザー初期化エラー: {str(e)}")
            # 仮のユーザー情報を設定
            st.session_state.user = {
                "user_id": str(uuid.uuid4()),
                "username": "ゲストユーザー",
                "xp_points": 0,
                "level": 0,
                "badges": [],
                "settings": {"notifications": True, "sound": True, "theme": "light"},
                "learning_paths": ["基礎思考力"]
            }

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

# カスタムCSSの適用
def apply_custom_css():
    """アプリにカスタムCSSを適用する"""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #4F8BF9;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #F0F2F6;
        align-self: flex-end;
    }
    .assistant-message {
        background-color: #E6F0FF;
        align-self: flex-start;
    }
    .message-content {
        display: flex;
        margin-top: 0.5rem;
    }
    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .thought-box {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        background-color: #E6F0FF;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .level-progress {
        height: 1.5rem;
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# メイン関数
def main():
    # データベース初期化
    init_database()
    
    # セッション状態の初期化
    init_session_state()
    
    # カスタムCSSの適用
    apply_custom_css()
    
    # アプリヘッダー
    st.markdown(f"<h1 class='main-header'>{APP_NAME}</h1>", unsafe_allow_html=True)

    # メインコンテンツ
    st.markdown("### ようこそ！")
    st.markdown("左のサイドバーから機能を選択してください。")
    
    # ユーザー情報表示
    if 'user' in st.session_state:
        user = st.session_state.user
        st.sidebar.markdown(f"### こんにちは、{user['username']}さん")
        st.sidebar.markdown(f"レベル: {user['level']}")
        st.sidebar.markdown(f"XP: {user['xp_points']}")
    
    # バージョン情報
    st.sidebar.markdown(f"<div style='position: fixed; bottom: 0; padding: 10px;'>v{APP_VERSION}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()