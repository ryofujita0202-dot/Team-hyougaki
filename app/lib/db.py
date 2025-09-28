from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
import os

# 本番環境でのデータベースURL設定
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./fish_tank.db")

# エンジン作成時の設定を改善
connect_args = {}
if "sqlite" in DB_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DB_URL, 
    echo=False, 
    connect_args=connect_args,
    pool_pre_ping=True  # 接続の健全性チェック
)

def init_db():
    """データベースとテーブルを初期化"""
    try:
        # モデルをインポートしてSQLModelに登録
        from . import models  # noqa: F401
        
        # テーブルが存在しない場合のみ作成
        SQLModel.metadata.create_all(engine)
        
        # 既存テーブルの互換性確保（カラム追加）
        ensure_db_compatibility()
        
    except Exception as e:
        print(f"データベース初期化エラー: {e}")
        # エラーが発生してもアプリは継続実行


def ensure_db_compatibility():
    """既存データベースとの互換性を確保"""
    try:
        with engine.begin() as conn:
            # 'view'テーブルの'comprehension'カラム確認・追加
            info = conn.execute(text("PRAGMA table_info('view')")).mappings().all()
            cols = [row.get('name') for row in info] if info else []
            if 'comprehension' not in cols:
                conn.execute(text('ALTER TABLE "view" ADD COLUMN comprehension INTEGER'))
                
            # 'fish'テーブルの'fish_color'カラム確認・追加
            info = conn.execute(text("PRAGMA table_info('fish')")).mappings().all()
            cols = [row.get('name') for row in info] if info else []
            if 'fish_color' not in cols:
                conn.execute(text('ALTER TABLE "fish" ADD COLUMN fish_color TEXT DEFAULT "#FF6B6B"'))
                
    except Exception as e:
        print(f"データベース互換性確保エラー: {e}")
        # エラーを無視してアプリを継続

def get_session():
    """データベースセッションを取得"""
    try:
        session = Session(engine)
        return session
    except Exception as e:
        print(f"セッション作成エラー: {e}")
        # 再試行
        return Session(engine)
