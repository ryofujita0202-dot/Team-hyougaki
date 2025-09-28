"""YouTube API クライアント（スタブ実装）"""

def search(query: str, max_results: int = 10) -> list[dict]:
    """YouTube動画検索（スタブ実装）"""
    return []

def get_video_meta(video_id: str) -> dict:
    """YouTube動画メタデータ取得（スタブ実装）"""
    return {
        "title": f"Video {video_id}",
        "channel_title": "Unknown Channel",
        "duration_seconds": 0,
        "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        "description": ""
    }