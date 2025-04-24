import streamlit as st
import ast
import operator as op
import re
import time
import uuid
import json
import numpy as np
import logging
from typing import Dict, Any, Optional, List, Union

# 定数
APP_NAME = "思考力マスター"
APP_VERSION = "1.0.1"
THEME_COLOR = "#4F8BF9"
MAX_HINT = 3

# 数式演算に使用する演算子マッピング
OPS = {
    ast.Add: op.add, 
    ast.Sub: op.sub, 
    ast.Mult: op.mul, 
    ast.Div: op.truediv,
    ast.USub: op.neg,
    ast.Pow: op.pow
}

# カテゴリアイコン
CATEGORY_ICONS = {
    "数で考える力": "🔢",
    "ことばで伝える力": "💬", 
    "しくみを見つける力": "🔍",
    "論理的思考力": "🧩",
    "分析力": "📈",
    "創造的思考力": "💡"
}

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

# 数式の安全な評価
def safe_eval(expr: str) -> Optional[float]:
    """数式を安全に評価する関数"""
    try:
        # 入力のクリーンアップ
        expr = expr.strip().replace('×', '*').replace('÷', '/').replace('^', '**')
        
        # 式の解析
        node = ast.parse(expr, mode='eval').body
        
        def _eval(node):
            """ASTノードを再帰的に評価"""
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                # 二項演算
                if type(node.op) not in OPS:
                    raise ValueError(f"サポートされていない演算: {type(node.op)}")
                return OPS[type(node.op)](_eval(node.left), _eval(node.right))
            elif isinstance(node, ast.UnaryOp):
                # 単項演算
                if type(node.op) not in OPS:
                    raise ValueError(f"サポートされていない演算: {type(node.op)}")
                return OPS[type(node.op)](_eval(node.operand))
            elif isinstance(node, ast.Constant):
                # Python 3.8以降向け
                return node.value
            else:
                raise ValueError(f"サポートされていない式: {type(node)}")
                
        return _eval(node)
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError) as e:
        logging.warning(f"式評価エラー: {str(e)} - 式: {expr}")
        return None

# テキスト正規化
def normalize_text(text: str) -> str:
    """テキストを正規化する関数"""
    if not text:
        return ""
    
    # 空白と改行の正規化
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 全角文字を半角に変換
    text = text.translate(str.maketrans({
        '　': ' ',
        '，': ',',
        '．': '.',
        '！': '!',
        '？': '?',
        '：': ':',
        '；': ';',
        '（': '(',
        '）': ')',
        '［': '[',
        '］': ']',
        '｛': '{',
        '｝': '}',
        '＋': '+',
        '－': '-',
        '＊': '*',
        '／': '/',
        '＝': '='
    }))
    
    return text.lower()

# 選択肢一致チェック
def check_choice_match(user_answer: str, correct_choices: List[str]) -> bool:
    """選択肢の一致をチェックする関数"""
    if not user_answer or not correct_choices:
        return False
    
    # 正規化
    user_norm = normalize_text(user_answer)
    choices_norm = [normalize_text(c) for c in correct_choices]
    
    # 完全一致または選択肢の値/キーの一致をチェック
    return user_norm in choices_norm

# 数値一致チェック
def check_numeric_match(user_answer: str, correct_value: Union[int, float, str], tolerance: float = 0.01) -> bool:
    """数値の一致をチェックする関数"""
    try:
        # 文字列から数値への変換
        user_value = float(normalize_text(user_answer).replace(',', ''))
        
        # 正解値も数値に変換
        if isinstance(correct_value, str):
            correct_value = float(normalize_text(correct_value).replace(',', ''))
        else:
            correct_value = float(correct_value)
        
        # 許容誤差内での一致チェック
        return abs(user_value - correct_value) <= tolerance
    except (ValueError, TypeError):
        return False

# テキスト一致チェック
def check_text_match(user_answer: str, correct_answer: str, fuzzy: bool = True) -> bool:
    """テキストの一致をチェックする関数"""
    if not user_answer or not correct_answer:
        return False
    
    # 正規化
    user_norm = normalize_text(user_answer)
    correct_norm = normalize_text(correct_answer)
    
    if fuzzy:
        # あいまい一致（正解が回答に含まれているか、または回答が正解に含まれている）
        return user_norm in correct_norm or correct_norm in user_norm
    else:
        # 厳密一致
        return user_norm == correct_norm

# ユーザーレベル計算
def calculate_user_level(xp_points: int) -> int:
    """XPポイントからユーザーレベルを計算"""
    for level, info in sorted(USER_LEVELS.items(), key=lambda x: x[0], reverse=True):
        if xp_points >= info["req"]:
            return level
    return 0

# 解答XP計算
def calculate_xp_reward(problem: Dict[str, Any], duration: float, hints_used: int) -> int:
    """問題解答からXPポイントを計算"""
    # 基本XP = 問題の難易度 * 10
    base_xp = problem.get("difficulty", 1) * 10
    
    # ヒント減少 = 使用ヒント数に応じて減少
    hint_penalty = hints_used * 2
    
    # 時間ボーナス = 素早く回答するほど増加
    difficulty_factor = problem.get("difficulty", 1)
    expected_time = difficulty_factor * 30  # 難易度に応じた期待解答時間（秒）
    
    time_bonus = 0
    if duration < expected_time:
        # 期待時間より早い場合、ボーナス
        time_bonus = int((expected_time - duration) / 5)
    
    # 最終XP = 基本XP - ヒント減少 + 時間ボーナス
    final_xp = max(5, base_xp - hint_penalty + time_bonus)
    
    return final_xp

# Lottieアニメーション読み込み
def load_lottie(url: str) -> Optional[Dict[str, Any]]:
    """URLからLottieアニメーションを読み込む"""
    try:
        import requests
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logging.error(f"Lottie読み込みエラー: {str(e)}")
        return None

# ストリーク更新
def update_streak(last_active: float) -> (bool, int):
    """ユーザーのストリーク日数を更新"""
    from datetime import datetime, timedelta
    
    now = time.time()
    last_active_date = datetime.fromtimestamp(last_active).date() 
    today = datetime.fromtimestamp(now).date()
    yesterday = today - timedelta(days=1)
    
    if last_active_date == today:
        # 既に今日活動済み
        return (False, 0)
    elif last_active_date == yesterday:
        # 昨日も活動していた
        return (True, 1)
    else:
        # 昨日活動していなかった
        return (True, 0)