import os
import json
import requests
import logging
import time
from typing import Dict, Any, Optional

# LLM APIレスポンス用のスタブデータ
STUB_RESPONSES = {
    "default": "追加の深掘りを提案します。この問題の解き方をもう少し考えてみましょう。",
    "hint": "もう少し別の視点から考えてみましょう。",
    "feedback": "良い答えですね！さらに発展させるなら、この考え方は他の問題にも応用できます。",
    "follow_up": "この問題と関連して、実生活ではどのような場面でこの考え方が役立つでしょうか？"
}

# LLM API呼び出し
def call_llm_api(prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    LLM API呼び出し関数
    将来的に実際のAPI（OpenAI, Anthropic, ローカルLlamaなど）に接続
    """
    api_key = os.getenv("LLM_API_KEY")
    api_endpoint = os.getenv("LLM_API_ENDPOINT")
    
    if not api_key or not api_endpoint:
        # API設定がない場合はスタブレスポンスを返す
        return get_canned_response(prompt)
    
    try:
        # API呼び出し用のペイロード作成
        payload = {
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0.7,
            "context": context or {}
        }
        
        # ヘッダー設定
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # APIリクエスト
        response = requests.post(
            api_endpoint,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("text", STUB_RESPONSES["default"])
        else:
            logging.error(f"LLM API エラー: ステータスコード {response.status_code}")
            return STUB_RESPONSES["default"]
    except Exception as e:
        logging.error(f"LLM API 呼び出しエラー: {str(e)}")
        return STUB_RESPONSES["default"]

# スタブレスポンスの取得
def get_canned_response(prompt: str) -> str:
    """
    プロンプトに基づいてスタブレスポンスを返す
    開発・テスト用
    """
    prompt_lower = prompt.lower()
    
    if "hint" in prompt_lower or "ヒント" in prompt_lower:
        return STUB_RESPONSES["hint"]
    elif "feedback" in prompt_lower or "フィードバック" in prompt_lower:
        return STUB_RESPONSES["feedback"]
    elif "follow" in prompt_lower or "follow-up" in prompt_lower or "続き" in prompt_lower:
        return STUB_RESPONSES["follow_up"]
    else:
        return STUB_RESPONSES["default"]

# 問題に対するフィードバック生成
def generate_problem_feedback(problem: Dict[str, Any], answer: str) -> str:
    """
    問題と回答に基づいたフィードバックを生成
    """
    prompt = f"""
    問題: {problem.get('question')}
    ユーザーの回答: {answer}
    正答: {problem.get('correct_answer', '不明')}
    
    この回答に対する教育的なフィードバックと、さらに深く考えるためのポイントを提案してください。
    """
    
    return call_llm_api(prompt, {
        "problem_type": problem.get("category", ""),
        "difficulty": problem.get("difficulty", 1),
        "tags": problem.get("tags", [])
    })

# ヒント生成
def generate_hint(problem: Dict[str, Any], hint_step: int) -> str:
    """
    問題に対するヒントを生成
    既存のヒントがある場合はそれを使い、ない場合は生成
    """
    if "hints" in problem and hint_step < len(problem["hints"]):
        return problem["hints"][hint_step]
    
    # ヒントがない場合はAPIで生成
    prompt = f"""
    問題: {problem.get('question')}
    
    この問題に対する{hint_step + 1}つ目のヒントを生成してください。
    直接的な答えは含めず、考え方のポイントを示唆するヒントにしてください。
    """
    
    return call_llm_api(prompt, {
        "problem_type": problem.get("category", ""),
        "difficulty": problem.get("difficulty", 1),
        "hint_level": hint_step + 1
    })

# フォローアップ質問生成
def generate_follow_up(problem: Dict[str, Any], answer: str) -> str:
    """
    問題と回答に基づいたフォローアップ質問を生成
    """
    if "follow_up" in problem and problem["follow_up"]:
        # ランダムに選択
        import random
        return random.choice(problem["follow_up"])
    
    # フォローアップがない場合はAPIで生成
    prompt = f"""
    問題: {problem.get('question')}
    ユーザーの回答: {answer}
    
    この問題と回答に関連して、さらに深く考えさせるフォローアップ質問を1つ生成してください。
    実生活での応用や、別の視点からの考察を促す質問が望ましいです。
    """
    
    return call_llm_api(prompt, {
        "problem_type": problem.get("category", ""),
        "tags": problem.get("tags", [])
    })