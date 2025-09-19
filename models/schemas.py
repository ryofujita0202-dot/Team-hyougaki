from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

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
    rating: Optional[int] = None
    note: Optional[str] = None
    summary_json: Optional[SummaryJson] = None
    wiki_summary: Optional[str] = None
    thumbnail_url: Optional[str] = None
    view_count_accum: int = 1
