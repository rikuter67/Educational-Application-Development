import streamlit as st
import json
from streamlit_lottie import st_lottie
import requests
import time
import logging
from pathlib import Path

# アプリ設定を最初に行う（他のStreamlitコマンドより前）
st.set_page_config(
    page_title="思考力マスター - ホーム",
    page_icon="🧠",
    layout="wide"
)

# 定数
APP_NAME = "思考力マスター"
CATEGORY_ICONS = {
    "数で考える力": "🔢",
    "ことばで伝える力": "💬", 
    "しくみを見つける力": "🔍",
    "論理的思考力": "🧩",
    "分析力": "📈",
    "創造的思考力": "💡"
}

# Lottieアニメーション読み込み
def load_lottie(url):
    """URLからLottieアニメーションを読み込む"""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logging.error(f"Lottie読み込みエラー: {str(e)}")
        return None

# セッション状態の確認と初期化
def check_session_state():
    """セッション状態が正しく初期化されているか確認"""
    if 'initialized' not in st.session_state:
        # app.pyが実行されていない場合の処理
        st.warning("アプリの初期化が完了していません。メインページからアクセスしてください。")
        st.session_state.initialized = True
        st.session_state.session_id = "temp_session"
        # 最小限の状態初期化
        if 'current_category' not in st.session_state:
            st.session_state.current_category = None
        if 'problem_index' not in st.session_state:
            st.session_state.problem_index = 0
        if 'hint_step' not in st.session_state:
            st.session_state.hint_step = 0
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'thought_logs' not in st.session_state:
            st.session_state.thought_logs = []
        if 'answer_submitted' not in st.session_state:
            st.session_state.answer_submitted = False

# カテゴリ選択処理
def handle_category_selection():
    """カテゴリ選択画面の表示と処理"""
    st.markdown("## カテゴリを選ぼう")
    
    # カテゴリカードの表示用コンテナ
    col1, col2, col3 = st.columns(3)
    
    # 基礎思考力カテゴリ
    with col1:
        st.markdown("### 🔢 数で考える力")
        st.markdown("数字やパターンを分析して解決する力を鍛えます。")
        if st.button("このカテゴリを選ぶ", key="cat_math"):
            st.session_state.current_category = "数で考える力"
            st.session_state.problem_index = 0
            st.session_state.hint_step = 0
            st.rerun()  # experimental_rerunからrerunに変更
    
    with col2:
        st.markdown("### 💬 ことばで伝える力")
        st.markdown("言葉の意味や論理を理解し表現する力を育みます。")
        if st.button("このカテゴリを選ぶ", key="cat_language"):
            st.session_state.current_category = "ことばで伝える力"
            st.session_state.problem_index = 0
            st.session_state.hint_step = 0
            st.rerun()  # 変更
    
    with col3:
        st.markdown("### 🔍 しくみを見つける力")
        st.markdown("物事の関係性やパターンを見抜く力を強化します。")
        if st.button("このカテゴリを選ぶ", key="cat_pattern"):
            st.session_state.current_category = "しくみを見つける力"
            st.session_state.problem_index = 0
            st.session_state.hint_step = 0
            st.rerun()  # 変更
    
    # 発展思考力カテゴリ
    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown("### 🧩 論理的思考力")
        st.markdown("筋道立てて考え、結論を導く力を磨きます。")
        if st.button("このカテゴリを選ぶ", key="cat_logic"):
            st.session_state.current_category = "論理的思考力"
            st.session_state.problem_index = 0
            st.session_state.hint_step = 0
            st.rerun()  # 変更
    
    with col5:
        st.markdown("### 📈 分析力")
        st.markdown("データや情報を整理して意味を見出す力を養います。")
        if st.button("このカテゴリを選ぶ", key="cat_analysis"):
            st.session_state.current_category = "分析力"
            st.session_state.problem_index = 0
            st.session_state.hint_step = 0
            st.rerun()  # 変更
    
    with col6:
        st.markdown("### 💡 創造的思考力")
        st.markdown("新しいアイデアや解決策を生み出す力を伸ばします。")
        if st.button("このカテゴリを選ぶ", key="cat_creative"):
            st.session_state.current_category = "創造的思考力"
            st.session_state.problem_index = 0
            st.session_state.hint_step = 0
            st.rerun()  # 変更

# ホーム画面メイン関数
def main():
    """ホーム画面のメイン処理"""
    # セッション状態の確認
    check_session_state()
    
    # ホーム画面ヘッダー
    st.markdown("# 思考力マスター ホーム")
    
    # 選択されたカテゴリがあるか確認
    if st.session_state.current_category:
        st.markdown(f"## 現在のカテゴリ: {CATEGORY_ICONS.get(st.session_state.current_category, '📝')} {st.session_state.current_category}")
        
        # 問題解決ページへのリンク
        if st.button("問題に挑戦する"):
            # 問題ページへリダイレクト
            st.markdown('<meta http-equiv="refresh" content="0;URL=./problem">', unsafe_allow_html=True)
            st.rerun()  # 変更
        
        # カテゴリ変更オプション
        if st.button("カテゴリを変更する"):
            st.session_state.current_category = None
            st.rerun()  # 変更
    else:
        # カテゴリが選択されていない場合、選択画面を表示
        # Lottieアニメーションの表示
        lottie_url = "https://assets1.lottiefiles.com/packages/lf20_zrqthn6o.json"
        lottie_json = load_lottie(lottie_url)
        if lottie_json:
            st_lottie(lottie_json, height=200, key="lottie")
        
        handle_category_selection()

# ページ実行
if __name__ == "__main__":
    main()