import streamlit as st
import json
import time
import uuid
import logging
from pathlib import Path
import sqlite3

# アプリ設定を最初に行う（他のStreamlitコマンドより前）
st.set_page_config(
    page_title="思考力マスター - 問題解決",
    page_icon="🧠",
    layout="wide"
)

# 定数
PROBLEM_JSON = "problems.json"
DB_PATH = "thinking_app.db"
MAX_HINT = 3
CATEGORY_ICONS = {
    "数で考える力": "🔢",
    "ことばで伝える力": "💬", 
    "しくみを見つける力": "🔍",
    "論理的思考力": "🧩",
    "分析力": "📈",
    "創造的思考力": "💡"
}

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)

# セッション状態の確認と初期化
def check_session_state():
    """セッション状態が正しく初期化されているか確認"""
    if 'initialized' not in st.session_state:
        st.warning("アプリの初期化が完了していません。メインページからアクセスしてください。")
        st.session_state.initialized = True
        st.session_state.session_id = "temp_session"
        
    # 問題解決に必要な状態変数の初期化
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
    if 'current_category' not in st.session_state:
        st.session_state.current_category = None
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()

# 問題データの読み込み
@st.cache_data(ttl=3600)
def load_problems():
    """問題データをJSONから読み込む（1時間キャッシュ）"""
    try:
        with open(PROBLEM_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"問題データロードエラー: {str(e)}")
        st.error(f"問題データロードエラー: {str(e)}")
        return []

# 現在のカテゴリの問題を取得
def get_category_problems():
    """現在選択されているカテゴリの問題一覧を取得"""
    problems = load_problems()
    if st.session_state.current_category:
        return [p for p in problems if p.get("category") == st.session_state.current_category]
    return []

# 現在の問題を取得
def get_current_problem():
    """現在の問題インデックスに対応する問題を取得"""
    problems = get_category_problems()
    if problems and 0 <= st.session_state.problem_index < len(problems):
        return problems[st.session_state.problem_index]
    return None

# チャットメッセージの表示
def display_chat_messages():
    """チャット履歴の表示"""
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <div class="message-content">{msg["text"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <div class="message-content">{msg["text"]}</div>
            </div>
            """, unsafe_allow_html=True)

# LLM 応答生成スタブ
def generate_reply(prompt: str) -> str:
    """LLM応答生成のスタブ関数（将来的にAPI連携）"""
    # 実際のLLM API呼び出しに置き換え予定
    return "追加の深掘りを提案します。この問題の解き方をもう少し考えてみましょう。物事を別の視点から見ることで新しい解決策が見つかることがあります。"

# ヒントボタンのコールバック
def on_hint_click():
    """ヒントボタンクリック時の処理"""
    problem = get_current_problem()
    if problem and "hints" in problem and st.session_state.hint_step < len(problem["hints"]):
        hint = problem["hints"][st.session_state.hint_step]
        st.session_state.chat_history.append({
            "role": "assistant",
            "text": f"ヒント {st.session_state.hint_step + 1}: {hint}",
            "timestamp": time.time()
        })
        st.session_state.hint_step += 1
        
        # ヒント使用をデータベースに記録
        try:
            save_session(
                st.session_state.session_id,
                st.session_state.user.get("user_id", "guest"),
                st.session_state.current_category,
                st.session_state.problem_index,
                st.session_state.hint_step
            )
        except Exception as e:
            logging.error(f"ヒント記録エラー: {str(e)}")

# 思考ログ追加のコールバック
def on_thought_submit():
    """思考ログ追加ボタンクリック時の処理"""
    thought_text = st.session_state.thought_input
    if thought_text:
        st.session_state.thought_logs.append(thought_text)
        st.session_state.thought_input = ""  # 入力欄をクリア
        
        # 思考ログをデータベースに保存
        try:
            save_thought_logs(
                st.session_state.session_id,
                get_current_problem().get("id", "unknown"),
                st.session_state.thought_logs
            )
        except Exception as e:
            logging.error(f"思考ログ保存エラー: {str(e)}")

# 回答処理
def process_answer(answer_text, problem):
    """回答処理と正誤判定"""
    # 回答が空なら処理しない
    if not answer_text:
        return
    
    # 回答をチャット履歴に追加
    st.session_state.chat_history.append({
        "role": "user",
        "text": answer_text,
        "timestamp": time.time()
    })
    
    # 正誤チェック（簡易実装）
    is_correct = False
    correct_answer = problem.get("correct_answer", "")
    
    if problem.get("answer_type") == "numeric":
        # 数値回答の場合
        try:
            user_answer = float(answer_text.strip().replace(',', ''))
            correct_val = float(str(correct_answer).replace(',', ''))
            is_correct = abs(user_answer - correct_val) < 0.01
        except (ValueError, TypeError):
            is_correct = False
    else:
        # テキスト回答の場合（単純文字列比較）
        is_correct = answer_text.strip().lower() == str(correct_answer).lower()
    
    # 回答結果のメッセージを追加
    if is_correct:
        response = f"正解です！ {problem.get('explanation', '')}"
    else:
        response = f"惜しいですね。もう一度考えてみましょう。"
    
    st.session_state.chat_history.append({
        "role": "assistant",
        "text": response,
        "timestamp": time.time()
    })
    
    # 正解の場合、深掘りフィードバックを提供
    if is_correct:
        feedback = generate_reply(f"Problem: {problem.get('question')} Answer: {answer_text}")
        st.session_state.chat_history.append({
            "role": "assistant", 
            "text": feedback,
            "timestamp": time.time()
        })
        
        # 問題解答記録を保存
        try:
            # 解答時間を計算
            duration = time.time() - st.session_state.start_time
            thought_length = sum(len(t) for t in st.session_state.thought_logs)
            
            attempt = {
                "attempt_id": str(uuid.uuid4()),
                "user_id": st.session_state.user.get("user_id", "guest"),
                "problem_id": problem.get("id", "unknown"),
                "category": problem.get("category", "unknown"),
                "timestamp": time.time(),
                "duration": duration,
                "is_correct": is_correct,
                "hints_used": st.session_state.hint_step,
                "thought_length": thought_length,
                "answer_text": answer_text
            }
            
            save_problem_attempt(attempt)
            
            # チャット履歴を保存
            save_chat_messages(
                st.session_state.session_id,
                problem.get("id", "unknown"),
                st.session_state.chat_history
            )
        except Exception as e:
            logging.error(f"解答保存エラー: {str(e)}")

# 次の問題へ移動するコールバック
def on_next_problem():
    """次の問題へ移動するボタンクリック時の処理"""
    problems = get_category_problems()
    if problems and st.session_state.problem_index < len(problems) - 1:
        st.session_state.problem_index += 1
        st.session_state.hint_step = 0
        st.session_state.chat_history = []
        st.session_state.thought_logs = []
        st.session_state.answer_submitted = False
        st.session_state.start_time = time.time()
        
        # セッション更新
        try:
            save_session(
                st.session_state.session_id,
                st.session_state.user.get("user_id", "guest"),
                st.session_state.current_category,
                st.session_state.problem_index,
                st.session_state.hint_step
            )
        except Exception as e:
            logging.error(f"セッション更新エラー: {str(e)}")
    else:
        # 全問題終了の処理
        st.session_state.all_complete = True

# 問題セクションの表示
def display_problem_section():
    """問題表示と回答入力セクション"""
    problem = get_current_problem()
    if not problem:
        st.warning("問題が見つかりません。カテゴリを選択してください。")
        if st.button("ホームに戻る"):
            st.markdown('<meta http-equiv="refresh" content="0;URL=./home">', unsafe_allow_html=True)
        return
    
    # 問題表示
    st.markdown(f"### {problem.get('category')} {CATEGORY_ICONS.get(problem.get('category'), '📝')}")
    st.markdown(f"**Q. {problem.get('question')}**")
    
    # チャット履歴の表示
    display_chat_messages()
    
    # 回答入力フォーム
    answer_key = f"answer_{problem.get('id', 'unknown')}"
    
    if not st.session_state.answer_submitted:
        st.text_area("あなたの回答", key=answer_key, height=100)
        
        def on_answer_submit():
            answer_text = st.session_state[answer_key]
            process_answer(answer_text, problem)
            st.session_state.answer_submitted = True
        
        st.button("回答する", on_click=on_answer_submit)
    
    # ヒントボタン（回答済みでなく、ヒントが残っている場合）
    if not st.session_state.answer_submitted and "hints" in problem and st.session_state.hint_step < len(problem["hints"]):
        st.button(f"ヒントを表示 ({st.session_state.hint_step + 1}/{len(problem['hints'])})", 
                on_click=on_hint_click)
    
    # 次の問題へ（回答済みの場合）
    if st.session_state.answer_submitted:
        problems = get_category_problems()
        if problems and st.session_state.problem_index < len(problems) - 1:
            st.button("次の問題へ", on_click=on_next_problem)
        else:
            st.success("おめでとうございます！すべての問題を完了しました。")
            if st.button("ホームに戻る"):
                st.markdown('<meta http-equiv="refresh" content="0;URL=./home">', unsafe_allow_html=True)

# 思考ログセクションの表示
def display_thought_log_section():
    """思考ログ表示と入力セクション"""
    st.markdown("### 思考ログ")
    st.markdown("問題を解く過程での考えを記録しましょう。")
    
    # 既存の思考ログを表示
    for i, thought in enumerate(st.session_state.thought_logs):
        st.text_area(f"思考 {i+1}", thought, height=100, disabled=True, key=f"thought_display_{i}")
    
    # 新しい思考を追加するフォーム
    st.text_area("新しい思考を追加", key="thought_input", height=100)
    st.button("思考を記録", on_click=on_thought_submit)

# データベース関連関数
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

# 問題ページのメイン関数
def main():
    """問題ページのメイン処理"""
    # セッション状態の確認
    check_session_state()
    
    # カテゴリが選択されていない場合
    if not st.session_state.current_category:
        st.warning("カテゴリが選択されていません。ホーム画面からカテゴリを選択してください。")
        if st.button("ホームに戻る"):
            st.markdown('<meta http-equiv="refresh" content="0;URL=./home">', unsafe_allow_html=True)
        return
    
    st.markdown(f"# 問題解決 - {st.session_state.current_category}")
    
    # 2カラムレイアウト
    col1, col2 = st.columns([7, 3])
    
    with col1:
        display_problem_section()
    
    with col2:
        display_thought_log_section()

# ページ実行
if __name__ == "__main__":
    main()