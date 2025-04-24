import streamlit as st
import json
import sqlite3
import time
from pathlib import Path

# 定数
DB_PATH = "thinking_app.db"
USER_LEVELS = {
    0: {"name": "初心者", "icon": "🌱", "req": 0},
    1: {"name": "探究者", "icon": "🔍", "req": 100}, 
    2: {"name": "思考家", "icon": "💭", "req": 300},
    3: {"name": "分析者", "icon": "📊", "req": 600},
    4: {"name": "論理家", "icon": "⚖️", "req": 1000},
    5: {"name": "戦略家", "icon": "♟️", "req": 1500},
    6: {"name": "賢者", "icon": "🧠", "req": 2500}
}

# バッジ情報
BADGES = {
    "first_correct": {"name": "ファーストステップ", "icon": "🥇", "desc": "初めての正解"},
    "streak_3": {"name": "3連続正解", "icon": "🔥", "desc": "3問連続で正解"},
    "streak_5": {"name": "5連続正解", "icon": "🔥🔥", "desc": "5問連続で正解"}, 
    "streak_10": {"name": "10連続正解", "icon": "🔥🔥🔥", "desc": "10問連続で正解"},
    "no_hint": {"name": "独力解決者", "icon": "💪", "desc": "ヒントなしで問題を解決"}, 
    "fast_solver": {"name": "スピード思考", "icon": "⚡", "desc": "60秒以内に正解"},
    "deep_thinker": {"name": "深い思考", "icon": "🧘", "desc": "300文字以上の思考ログを残す"},
    "complete_category": {"name": "カテゴリマスター", "icon": "🏆", "desc": "カテゴリ内の全問題を解く"},
    "all_categories": {"name": "全領域マスター", "icon": "👑", "desc": "すべてのカテゴリで問題を解く"}
}

# セッション状態の確認
def check_session_state():
    if 'initialized' not in st.session_state:
        st.warning("アプリの初期化が完了していません。メインページからアクセスしてください。")
        st.session_state.initialized = True
        st.session_state.session_id = "temp_session"
        if 'user' not in st.session_state:
            st.session_state.user = {
                "user_id": "temp_user",
                "username": "ゲストユーザー",
                "xp_points": 0,
                "level": 0,
                "badges": []
            }

# ユーザープロフィールの更新処理
def update_user_profile():
    try:
        new_username = st.session_state.username_input
        if new_username and new_username != st.session_state.user["username"]:
            st.session_state.user["username"] = new_username
            
            # データベースに保存
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET username = ? WHERE user_id = ?",
                (new_username, st.session_state.user["user_id"])
            )
            conn.commit()
            conn.close()
            
            st.success("プロフィールを更新しました！")
            st.experimental_rerun()
    except Exception as e:
        st.error(f"プロフィール更新エラー: {e}")

# レベル情報を取得
def get_level_info(level):
    return USER_LEVELS.get(level, USER_LEVELS[0])

# 次のレベル情報を取得
def get_next_level_info(level):
    next_level = level + 1
    if next_level in USER_LEVELS:
        return USER_LEVELS[next_level]
    return None

# レベル進捗を計算
def calculate_level_progress(xp_points, level):
    current_req = USER_LEVELS.get(level, {"req": 0})["req"]
    next_level = level + 1
    
    if next_level in USER_LEVELS:
        next_req = USER_LEVELS[next_level]["req"]
        points_in_level = xp_points - current_req
        level_range = next_req - current_req
        return min(1.0, points_in_level / level_range)
    
    return 1.0  # 最大レベル達成

# ユーザープロフィール表示
def display_user_profile():
    user = st.session_state.user
    
    # プロフィール基本情報
    st.markdown("## ユーザープロフィール")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # ユーザーアイコン（仮）
        st.markdown("### 🧑‍🎓")
    
    with col2:
        # ユーザー名（編集可能）
        st.text_input("ユーザー名", 
                     value=user.get("username", "ゲストユーザー"), 
                     key="username_input")
        
        if st.button("更新"):
            update_user_profile()
    
    # レベル情報
    st.markdown("---")
    st.markdown("## レベルと経験値")
    
    level = user.get("level", 0)
    xp = user.get("xp_points", 0)
    
    level_info = get_level_info(level)
    next_level_info = get_next_level_info(level)
    
    st.markdown(f"### {level_info['icon']} レベル {level}: {level_info['name']}")
    
    # 経験値プログレスバー
    progress = calculate_level_progress(xp, level)
    st.progress(progress)
    
    if next_level_info:
        st.markdown(f"次のレベル: {next_level_info['name']} ({next_level_info['req'] - xp} XP必要)")
    else:
        st.markdown("最大レベルに達しています！")
    
    # バッジコレクション
    st.markdown("---")
    st.markdown("## バッジコレクション")
    
    badges = user.get("badges", [])
    
    if not badges:
        st.info("まだバッジを獲得していません。問題を解いて獲得しましょう！")
    else:
        # バッジを3列で表示
        cols = st.columns(3)
        for i, badge_id in enumerate(badges):
            badge = BADGES.get(badge_id)
            if badge:
                with cols[i % 3]:
                    st.markdown(f"### {badge['icon']} {badge['name']}")
                    st.markdown(f"{badge['desc']}")
    
    # 獲得可能なバッジ
    st.markdown("### 獲得可能なバッジ")
    remaining_badges = [badge_id for badge_id in BADGES if badge_id not in badges]
    
    if not remaining_badges:
        st.success("すべてのバッジを獲得しました！おめでとうございます！")
    else:
        # 残りのバッジを3列で表示
        cols = st.columns(3)
        for i, badge_id in enumerate(remaining_badges[:6]):  # 最大6つまで表示
            badge = BADGES.get(badge_id)
            if badge:
                with cols[i % 3]:
                    st.markdown(f"### {badge['icon']} {badge['name']}")
                    st.markdown(f"*{badge['desc']}*")
                    st.markdown("*（未獲得）*")
        
        if len(remaining_badges) > 6:
            st.markdown(f"*他 {len(remaining_badges) - 6} 個のバッジが獲得可能です。*")

# プロフィールページのメイン関数
def main():
    # セッション状態の確認
    check_session_state()
    
    st.markdown("# マイプロフィール")
    
    if 'user' in st.session_state:
        display_user_profile()
    else:
        st.error("ユーザー情報が見つかりません。メインページからやり直してください。")
        if st.button("ホームに戻る"):
            st.markdown('<meta http-equiv="refresh" content="0;URL=./home">', unsafe_allow_html=True)

# ページ実行
if __name__ == "__main__":
    main()