"""Supabaseのデータベース操作"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import streamlit as st
from utils.supabase_client import get_supabase_client
from models.schemas import ViewLog

def save_view_log(log: ViewLog) -> bool:
    """視聴ログを保存"""
    try:
        supabase = get_supabase_client()
        
        # ViewLogをdictに変換
        log_data = log.model_dump()
        
        # datetimeオブジェクトを文字列に変換
        if isinstance(log_data['watched_at'], datetime):
            log_data['watched_at'] = log_data['watched_at'].isoformat()
        
        # summary_jsonを適切に処理
        if log_data.get('summary_json'):
            log_data['summary_json'] = log_data['summary_json'].model_dump()
        
        response = supabase.table("view_log").insert(log_data).execute()
        return len(response.data) > 0
        
    except Exception as e:
        st.error(f"データ保存エラー: {str(e)}")
        return False

def fetch_view_logs(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """ユーザーの視聴ログを取得"""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("view_log")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("watched_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return response.data
        
    except Exception as e:
        st.error(f"データ取得エラー: {str(e)}")
        return []

def get_user_stats(user_id: str) -> Dict[str, Any]:
    """ユーザーの統計情報を取得（動的魚生成用の詳細統計も含む）"""
    try:
        supabase = get_supabase_client()
        
        # 視聴ログの詳細データを取得
        response = supabase.table("view_log")\
            .select("view_count_accum, watch_seconds, rating, comprehension_level, watched_at, video_id, note")\
            .eq("user_id", user_id)\
            .execute()
        
        if not response.data:
            return {
                "total_videos": 0, 
                "total_watch_time": 0, 
                "total_views": 0,
                "avg_rating": 1,
                "avg_comprehension": 1,
                "total_sessions": 0,
                "days_since_last": 999,
                # 新しい統計項目
                "learning_consistency": 0.0,
                "preferred_genres": [],
                "peak_learning_hours": [],
                "comprehension_trend": "stable",
                "engagement_score": 0.0
            }
        
        logs = response.data
        total_videos = len(set(log.get("video_id", "") for log in logs))  # ユニーク動画数
        total_sessions = len(logs)  # 総セッション数
        total_watch_time = sum(log.get("watch_seconds", 0) or 0 for log in logs)
        total_views = sum(log.get("view_count_accum", 1) for log in logs)
        
        # 平均評価と理解度
        ratings = [log.get("rating") for log in logs if log.get("rating")]
        comprehensions = [log.get("comprehension_level") for log in logs if log.get("comprehension_level")]
        
        avg_rating = sum(ratings) / max(len(ratings), 1) if ratings else 1
        avg_comprehension = sum(comprehensions) / max(len(comprehensions), 1) if comprehensions else 1
        
        # 最後の視聴からの日数
        from datetime import datetime, timezone, timedelta
        latest_dates = []
        for log in logs:
            if log.get("watched_at"):
                try:
                    watch_date = datetime.fromisoformat(log["watched_at"].replace('Z', '+00:00'))
                    latest_dates.append(watch_date)
                except:
                    pass
        
        if latest_dates:
            latest_watch = max(latest_dates)
            days_since_last = (datetime.now(timezone.utc) - latest_watch).days
        else:
            days_since_last = 999

        # 新しい統計計算
        # 1. 学習の一貫性（過去30日間の学習頻度）
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_logs = [log for log in logs if log.get("watched_at") and 
                      datetime.fromisoformat(log["watched_at"].replace('Z', '+00:00')) > thirty_days_ago]
        learning_consistency = min(len(recent_logs) / 15.0, 1.0)  # 理想は30日で15回
        
        # 2. 理解度のトレンド分析
        if len(comprehensions) >= 3:
            recent_comprehensions = comprehensions[-5:]  # 最新5回
            early_avg = sum(comprehensions[:len(comprehensions)//2]) / max(len(comprehensions)//2, 1)
            recent_avg = sum(recent_comprehensions) / max(len(recent_comprehensions), 1)
            
            if recent_avg > early_avg + 0.3:
                comprehension_trend = "improving"
            elif recent_avg < early_avg - 0.3:
                comprehension_trend = "declining"
            else:
                comprehension_trend = "stable"
        else:
            comprehension_trend = "insufficient_data"
        
        # 3. エンゲージメントスコア（視聴時間 + 理解度 + 一貫性）
        time_score = min(total_watch_time / 3600.0 / 10, 1.0)  # 10時間で満点
        comprehension_score = (avg_comprehension - 1) / 2.0  # 1-3を0-1に正規化
        engagement_score = (time_score + comprehension_score + learning_consistency) / 3.0
        
        # 4. 時間帯分析（学習のピーク時間）
        hours = []
        for log in logs:
            if log.get("watched_at"):
                try:
                    watch_date = datetime.fromisoformat(log["watched_at"].replace('Z', '+00:00'))
                    hours.append(watch_date.hour)
                except:
                    pass
        
        # 時間帯別の学習頻度
        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # トップ3の時間帯
        peak_learning_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_learning_hours = [f"{hour}:00" for hour, count in peak_learning_hours]
        
        return {
            "total_videos": total_videos,
            "total_watch_time": total_watch_time,
            "total_views": total_views,
            "avg_rating": avg_rating,
            "avg_comprehension": avg_comprehension,
            "total_sessions": total_sessions,
            "days_since_last": days_since_last,
            # 新しい統計項目
            "learning_consistency": learning_consistency,
            "preferred_genres": [],  # 後で実装
            "peak_learning_hours": peak_learning_hours,
            "comprehension_trend": comprehension_trend,
            "engagement_score": engagement_score
        }
        
    except Exception as e:
        st.error(f"統計取得エラー: {str(e)}")
        return {
            "total_videos": 0, 
            "total_watch_time": 0, 
            "total_views": 0,
            "avg_rating": 1,
            "avg_comprehension": 1,
            "total_sessions": 0,
            "days_since_last": 999,
            # 新しい統計項目
            "learning_consistency": 0.0,
            "preferred_genres": [],
            "peak_learning_hours": [],
            "comprehension_trend": "stable",
            "engagement_score": 0.0
        }

def update_view_count(video_id: str, user_id: str) -> bool:
    """視聴回数を更新"""
    try:
        supabase = get_supabase_client()
        
        # 既存のログを取得
        response = supabase.table("view_log")\
            .select("*")\
            .eq("video_id", video_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if response.data:
            # 既存のログがある場合、view_count_accumを更新
            log = response.data[0]
            new_count = log.get("view_count_accum", 1) + 1
            
            supabase.table("view_log")\
                .update({"view_count_accum": new_count})\
                .eq("id", log["id"])\
                .execute()
        
        return True
        
    except Exception as e:
        st.error(f"視聴回数更新エラー: {str(e)}")
        return False

def search_view_logs(user_id: str, query: str = "", rating_filter: Optional[int] = None) -> List[Dict[str, Any]]:
    """視聴ログを検索・フィルタ"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        # 基本クエリ
        db_query = supabase.table("view_log")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("watched_at", desc=True)
        
        # 評価フィルタ
        if rating_filter is not None:
            db_query = db_query.eq("rating", rating_filter)
        
        response = db_query.execute()
        
        # テキスト検索（クライアント側で実装）
        if query:
            filtered_data = []
            for log in response.data:
                # タイトル、メモ、要約などで検索
                searchable_text = " ".join([
                    log.get("note", ""),
                    log.get("wiki_summary", ""),
                    str(log.get("summary_json", {}))
                ]).lower()
                
                if query.lower() in searchable_text:
                    filtered_data.append(log)
            
            return filtered_data
        
        return response.data
        
    except Exception as e:
        st.error(f"検索エラー: {str(e)}")
        return []

def get_user_learning_patterns(user_id: str) -> Dict[str, Any]:
    """ユーザーの学習パターンを詳細分析（魚生成用）"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return {}
        
        # 過去3ヶ月の学習データを取得
        from datetime import datetime, timezone, timedelta
        three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
        
        response = supabase.table("view_log")\
            .select("*")\
            .eq("user_id", user_id)\
            .gte("watched_at", three_months_ago.isoformat())\
            .execute()
        
        logs = response.data or []
        
        # 学習パターン分析
        patterns = {
            "learning_style": "balanced",  # focused, varied, balanced
            "preferred_difficulty": "medium",  # easy, medium, hard
            "learning_frequency": "regular",  # sporadic, regular, intensive
            "progress_speed": "steady",  # fast, steady, slow
            "favorite_topics": [],
            "learning_streaks": 0,
            "best_performance_time": "morning"  # morning, afternoon, evening, night
        }
        
        if not logs:
            return patterns
        
        # 理解度分析
        comprehensions = [log.get("comprehension_level") for log in logs if log.get("comprehension_level")]
        if comprehensions:
            avg_comp = sum(comprehensions) / len(comprehensions)
            if avg_comp <= 1.5:
                patterns["preferred_difficulty"] = "easy"
            elif avg_comp >= 2.5:
                patterns["preferred_difficulty"] = "hard"
            else:
                patterns["preferred_difficulty"] = "medium"
        
        # 学習頻度パターン
        dates = []
        for log in logs:
            if log.get("watched_at"):
                try:
                    date = datetime.fromisoformat(log["watched_at"].replace('Z', '+00:00')).date()
                    dates.append(date)
                except:
                    pass
        
        unique_dates = set(dates)
        if len(unique_dates) >= 60:  # 60日以上
            patterns["learning_frequency"] = "intensive"
        elif len(unique_dates) >= 20:  # 20日以上
            patterns["learning_frequency"] = "regular"
        else:
            patterns["learning_frequency"] = "sporadic"
        
        # 連続学習日数（ストリーク）
        if dates:
            dates.sort(reverse=True)
            streak = 1
            for i in range(1, len(dates)):
                if (dates[i-1] - dates[i]).days == 1:
                    streak += 1
                else:
                    break
            patterns["learning_streaks"] = streak
        
        # 時間帯分析
        hours = []
        for log in logs:
            if log.get("watched_at"):
                try:
                    hour = datetime.fromisoformat(log["watched_at"].replace('Z', '+00:00')).hour
                    hours.append(hour)
                except:
                    pass
        
        if hours:
            hour_counts = {}
            for hour in hours:
                if 5 <= hour < 12:
                    time_period = "morning"
                elif 12 <= hour < 17:
                    time_period = "afternoon" 
                elif 17 <= hour < 21:
                    time_period = "evening"
                else:
                    time_period = "night"
                
                hour_counts[time_period] = hour_counts.get(time_period, 0) + 1
            
            patterns["best_performance_time"] = max(hour_counts.keys(), key=lambda k: hour_counts[k])
        
        return patterns
        
    except Exception as e:
        st.error(f"学習パターン分析エラー: {str(e)}")
        return {
            "learning_style": "balanced",
            "preferred_difficulty": "medium",
            "learning_frequency": "regular",
            "progress_speed": "steady",
            "favorite_topics": [],
            "learning_streaks": 0,
            "best_performance_time": "morning"
        }

def get_all_users_stats() -> List[Dict[str, Any]]:
    """全ユーザーの統計を取得（ランキング用）"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []
        
        # 全ユーザーの基本情報を取得
        users_response = supabase.table("app_user")\
            .select("auth_user_id, display_name")\
            .execute()
        
        all_stats = []
        for user in users_response.data or []:
            user_id = user["auth_user_id"]
            stats = get_user_stats(user_id)
            stats["user_id"] = user_id
            stats["display_name"] = user.get("display_name", "Unknown")
            all_stats.append(stats)
        
        return all_stats
        
    except Exception as e:
        st.error(f"全体統計取得エラー: {str(e)}")
        return []