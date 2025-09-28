from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class ComprehensionLevel(Enum):
    """理解度レベル"""
    UNDERSTOOD = 1  # ①覚えた
    NORMAL = 2      # ②普通
    NOT_UNDERSTOOD = 3  # ③覚えていない

class SummaryJson(BaseModel):
    points: List[str] = []
    three_lines: List[str] = []
    chapters: List[str] = []
    quotes: Optional[List[Dict[str, Any]]] = None

class ViewLog(BaseModel):
    id: Optional[str] = None
    user_id: str
    video_id: str
    watched_at: datetime
    watch_seconds: Optional[int] = None
    rating: Optional[int] = None  # 1-5の従来評価（互換性のため残す）
    comprehension_level: Optional[ComprehensionLevel] = None  # 新しい理解度評価
    note: Optional[str] = None
    summary_json: Optional[SummaryJson] = None
    wiki_summary: Optional[str] = None
    thumbnail_url: Optional[str] = None
    view_count_accum: int = 1
    
    @property
    def comprehension_text(self) -> str:
        """理解度のテキスト表現"""
        if self.comprehension_level:
            mapping = {
                ComprehensionLevel.UNDERSTOOD: "①覚えた",
                ComprehensionLevel.NORMAL: "②普通", 
                ComprehensionLevel.NOT_UNDERSTOOD: "③覚えていない"
            }
            return mapping.get(self.comprehension_level, "未評価")
        return "未評価"

class VideoMeta(BaseModel):
    """YouTube動画のメタデータ"""
    video_id: str
    title: str
    channel_title: Optional[str] = None
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None