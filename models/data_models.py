from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional, Union
import time
import json

# 問題データモデル
@dataclass
class Problem:
    id: str
    category: str
    question: str  
    hints: List[str]
    follow_up: List[str]
    tags: List[str]
    difficulty: int = 1  # 1-5のスケール
    answer_type: str = "text"  # 'numeric', 'text', 'multi_choice'
    correct_answer: Optional[Union[float, str, List[str]]] = None
    explanation: Optional[str] = None
    related_problems: List[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Problem':
        return cls(
            id=data["id"],
            category=data["category"],
            question=data["question"],  
            hints=data.get("hints", []),
            follow_up=data.get("follow_up", []),
            tags=data.get("tags", []),
            difficulty=data.get("difficulty", 1),
            answer_type=data.get("answer_type", "text"),
            correct_answer=data.get("correct_answer"), 
            explanation=data.get("explanation"),
            related_problems=data.get("related_problems", [])
        )

# チャットメッセージモデル
@dataclass  
class ChatMessage:
    role: str  # 'user' または 'assistant'
    text: str
    timestamp: float = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "text": self.text,
            "timestamp": self.timestamp  
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':  
        return cls(
            role=data["role"],
            text=data["text"],
            timestamp=data.get("timestamp", time.time())  
        )

# ユーザープロファイルモデル
@dataclass
class UserProfile:
    user_id: str
    username: str
    created_at: float  
    xp_points: int = 0
    level: int = 0
    streak_days: int = 0  
    last_active: float = None
    badges: List[str] = None
    settings: Dict[str, Any] = None
    learning_paths: List[str] = None
    
    def __post_init__(self):
        if self.badges is None:
            self.badges = []
        if self.settings is None:  
            self.settings = {"notifications": True, "sound": True, "theme": "light"}
        if self.learning_paths is None:
            self.learning_paths = ["基礎思考力"] 
        if self.last_active is None:
            self.last_active = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "created_at": self.created_at,
            "xp_points": self.xp_points,
            "level": self.level,
            "streak_days": self.streak_days,
            "last_active": self.last_active,
            "badges": self.badges,  
            "settings": self.settings,
            "learning_paths": self.learning_paths
        }
    
    @classmethod  
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        return cls(
            user_id=data["user_id"],  
            username=data["username"],
            created_at=data["created_at"],
            xp_points=data.get("xp_points", 0),
            level=data.get("level", 0),
            streak_days=data.get("streak_days", 0),
            last_active=data.get("last_active", time.time()),  
            badges=data.get("badges", []),
            settings=data.get("settings", {"notifications": True, "sound": True, "theme": "light"}),  
            learning_paths=data.get("learning_paths", ["基礎思考力"]) 
        )

# 問題解答記録モデル
@dataclass
class ProblemAttempt:
    attempt_id: str 
    user_id: str
    problem_id: str
    category: str
    timestamp: float
    duration: float  # 解答時間（秒）
    is_correct: bool
    hints_used: int
    thought_length: int  # 思考ログの文字数
    answer_text: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "user_id": self.user_id, 
            "problem_id": self.problem_id,
            "category": self.category,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "is_correct": self.is_correct,
            "hints_used": self.hints_used,
            "thought_length": self.thought_length,
            "answer_text": self.answer_text
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProblemAttempt':
        return cls(
            attempt_id=data["attempt_id"],
            user_id=data["user_id"],
            problem_id=data["problem_id"], 
            category=data["category"],
            timestamp=data["timestamp"],
            duration=data["duration"],
            is_correct=data["is_correct"], 
            hints_used=data["hints_used"],
            thought_length=data["thought_length"],
            answer_text=data["answer_text"]
        )