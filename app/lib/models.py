from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List

class Video(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    video_id: str
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    views: List["View"] = Relationship(back_populates="video")
    fish: Optional["Fish"] = Relationship(back_populates="video")

class View(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="video.id")
    viewed_at: datetime = Field(default_factory=datetime.utcnow)
    duration_sec: Optional[int] = None
    comprehension: Optional[int] = None  # 1..3, 登録時/視聴時の理解度
    note: Optional[str] = None
    video: "Video" = Relationship(back_populates="views")

class Fish(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="video.id", unique=True)
    s: float = 0.7               # 記憶強度(0..1)
    health: int = 70             # 0..100
    weight_g: int = 100
    last_update: datetime = Field(default_factory=datetime.utcnow)
    status: str = "alive"        # 'alive'|'weak'|'dead'
    next_due: Optional[datetime] = None
    fish_color: str = "#FF6B6B"  # 金魚の色（HEXコード）
    video: "Video" = Relationship(back_populates="fish")
