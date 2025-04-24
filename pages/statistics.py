import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import time
from datetime import datetime, timedelta

# 定数
DB_PATH = "thinking_app.db"
CATEGORY_ICONS = {
    "数で考える力": "🔢",
    "ことばで伝える力": "💬", 
    "しくみを見つける力": "🔍",
    "論理的思考力": "🧩",
    "分析力": "📈",
    "創造的思考力": "💡"
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
                "username": "ゲストユーザー"
            }

# ユーザー統計の取得
def get_user_stats(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
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
        
        overall = dict(cursor.fetchone() or {
            "total_attempts": 0,
            "correct_answers": 0,
            "avg_correct_time": 0,
            "total_hints": 0,
            "avg_thought_length": 0
        })
        
        # 成功率の計算
        if overall.get("total_attempts"):
            overall["success_rate"] = (overall.get("correct_answers", 0) / overall.get("total_attempts", 1)) * 100
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
        
        conn.close()
        
        return {
            "overall": overall,
            "categories": categories,
            "recent": recent,
            "daily": daily  
        }
    except sqlite3.Error as e:
        st.error(f"統計データ取得エラー: {e}")
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

# 統計ダッシュボードの表示
def display_statistics_dashboard(stats):
    # 全体サマリー
    st.markdown("## 学習サマリー")
    
    overall = stats["overall"]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 挑戦した問題")
        st.markdown(f"# {overall.get('total_attempts', 0)}")
    
    with col2:
        st.markdown("### 正解率")
        success_rate = overall.get('success_rate', 0)
        st.markdown(f"# {success_rate:.1f}%")
    
    with col3:
        st.markdown("### 平均解答時間")
        avg_time = overall.get('avg_correct_time', 0)
        st.markdown(f"# {avg_time:.1f}秒")
    
    with col4:
        st.markdown("### 使用ヒント数")
        st.markdown(f"# {overall.get('total_hints', 0)}")
    
    # カテゴリ別パフォーマンス
    st.markdown("---")
    st.markdown("## カテゴリ別パフォーマンス")
    
    categories = stats["categories"]
    
    if not categories:
        st.info("まだどのカテゴリの問題にも挑戦していません。")
    else:
        # カテゴリデータをDataFrameに変換
        df_categories = pd.DataFrame(categories)
        
        # 正解率を計算
        df_categories['success_rate'] = (df_categories['correct'] / df_categories['attempts']) * 100
        
        # カテゴリアイコンを追加
        df_categories['icon'] = df_categories['category'].map(lambda x: CATEGORY_ICONS.get(x, '📝'))
        df_categories['category_with_icon'] = df_categories['icon'] + ' ' + df_categories['category']
        
        # グラフ作成
        fig = px.bar(
            df_categories,
            x='category_with_icon',
            y='attempts',
            color='success_rate',
            color_continuous_scale='Viridis',
            labels={'attempts': '挑戦回数', 'category_with_icon': 'カテゴリ', 'success_rate': '正解率 (%)'},
            title='カテゴリ別の挑戦回数と正解率'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 学習傾向の時系列グラフ
    st.markdown("---")
    st.markdown("## 学習傾向")
    
    daily = stats["daily"]
    
    if not daily:
        st.info("過去30日間の学習データがありません。")
    else:
        # 日別データをDataFrameに変換
        df_daily = pd.DataFrame(daily)
        
        # 日付を適切な形式に変換
        df_daily['day'] = pd.to_datetime(df_daily['day'])
        
        # 正解率を計算
        df_daily['success_rate'] = (df_daily['correct'] / df_daily['attempts']) * 100
        
        # 日付の範囲を作成（データがない日も含む）
        today = datetime.now().date()
        date_range = pd.date_range(end=today, periods=30, freq='D')
        df_date_range = pd.DataFrame({'day': date_range})
        
        # 完全なデータセットを作成（データがない日は0）
        df_complete = df_date_range.merge(df_daily, on='day', how='left').fillna(0)
        
        # グラフ作成（挑戦回数と正解数）
        fig1 = px.line(
            df_complete,
            x='day',
            y=['attempts', 'correct'],
            labels={'day': '日付', 'value': '回数', 'variable': '種類'},
            title='日別の挑戦回数と正解数',
            color_discrete_sequence=['#636EFA', '#00CC96']
        )
        
        fig1.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ))
        
        st.plotly_chart(fig1, use_container_width=True)
    
    # 最近の活動履歴
    st.markdown("---")
    st.markdown("## 最近の活動")
    
    recent = stats["recent"]
    
    if not recent:
        st.info("最近の活動記録がありません。")
    else:
        # データをDataFrameに変換
        df_recent = pd.DataFrame(recent)
        
        # タイムスタンプを読みやすい形式に変換
        df_recent['datetime'] = pd.to_datetime(df_recent['timestamp'], unit='s')
        df_recent['formatted_time'] = df_recent['datetime'].dt.strftime('%Y-%m-%d %H:%M')
        
        # 正誤を分かりやすい表記に
        df_recent['result'] = df_recent['is_correct'].apply(lambda x: '✅ 正解' if x else '❌ 不正解')
        
        # 表示するデータを整形
        display_df = df_recent[['formatted_time', 'category', 'result', 'duration', 'hints_used']]
        display_df.columns = ['日時', 'カテゴリ', '結果', '所要時間(秒)', '使用ヒント数']
        
        st.dataframe(display_df, use_container_width=True)

# 統計ページのメイン関数
def main():
    # セッション状態の確認
    check_session_state()
    
    st.markdown("# 学習統計")
    
    if 'user' in st.session_state:
        user = st.session_state.user
        st.markdown(f"## {user.get('username', 'ゲスト')}さんの学習分析")
        
        # 統計データの取得
        stats = get_user_stats(user.get("user_id", "temp_user"))
        
        # 統計ダッシュボードの表示
        display_statistics_dashboard(stats)
    else:
        st.error("ユーザー情報が見つかりません。メインページからやり直してください。")
        if st.button("ホームに戻る"):
            st.markdown('<meta http-equiv="refresh" content="0;URL=./home">', unsafe_allow_html=True)

# ページ実行
if __name__ == "__main__":
    main()