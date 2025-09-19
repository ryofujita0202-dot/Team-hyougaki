from dataclasses import dataclass
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

@dataclass
class Settings:
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    GOOGLE_AI_STUDIO_API_KEY: str = os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

settings = Settings()


git commit -m "環境変数・定数の読み込み／設定"
git push
