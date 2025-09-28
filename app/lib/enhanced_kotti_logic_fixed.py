"""
Supabaseデータ連動型こってぃくん画像生成ロジック
ユーザーの学習進度・理解度・連続学習を元にこってぃくんの進化を決定
"""
import streamlit as st
from typing import Dict, Any, Optional
import sys
import os

# パス追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from utils.supabase_client import get_supabase_client
except ImportError:
    # テスト環境やインポートエラー時のフォールバック
    def get_supabase_client():
        return None

from datetime import datetime, timedelta


def get_enhanced_kotti_state(user_id: str, video_id: Optional[int], base_stage: int = 1) -> Dict[str, Any]:
    """
    ユーザーの学習データを元にこってぃくんの状態を決定
    
    Args:
        user_id: ユーザーID
        video_id: 動画ID（任意）
        base_stage: 基本段階
        
    Returns:
        こってぃくんの状態辞書（stage, special_effects, bonus_size, achievements）
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return {'stage': base_stage, 'special_effects': None, 'bonus_size': 1.0, 'achievements': []}

        # ユーザー学習統計を取得
        user_stats = get_user_learning_stats(user_id)
        
        # 動画進度情報を取得（任意）
        video_history = []
        if video_id:
            try:
                video_response = supabase.table('user_video_progress').select('*') \
                    .eq('user_id', user_id) \
                    .eq('video_id', video_id) \
                    .execute()
                video_history = video_response.data if video_response.data else []
            except Exception:
                video_history = []

        # 各種ボーナス計算
        level_bonus = calculate_level_bonus(user_stats)
        
        # 連続学習ボーナス
        streak_bonus = calculate_streak_bonus(user_stats.get('learning_streak', 0))
        
        # 理解度ボーナス
        comprehension_bonus = calculate_comprehension_bonus(
            user_stats.get('avg_comprehension_score', 0)
        )
        
        # 健康度ベースの段階は変更せず、特殊効果・サイズのみ拡張
        # （健康度はforgetting.pyで科学的に計算されているため、それを尊重）
        enhanced_stage = base_stage  # 健康度ベースのstageを維持
        
        # 特殊エフェクト決定
        special_effects = determine_special_effects(user_stats, enhanced_stage)
        
        # サイズボーナス決定
        size_bonus = calculate_size_bonus(user_stats, enhanced_stage)
        
        # 実績取得
        achievements = get_user_achievements(user_stats)
        
        return {
            'stage': enhanced_stage,
            'special_effects': special_effects,
            'bonus_size': size_bonus,
            'achievements': achievements
        }
        
    except Exception as e:
        st.warning(f"Supabase連動エラー: {e}")
        return {'stage': base_stage, 'special_effects': None, 'bonus_size': 1.0, 'achievements': []}


def get_user_learning_stats(user_id: str) -> Dict[str, Any]:
    """ユーザーの学習統計を取得"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return {}
            
        response = supabase.table('user_learning_stats').select('*') \
            .eq('user_id', user_id) \
            .single() \
            .execute()
        
        return response.data if response.data else {}
    except Exception:
        return {}


def calculate_level_bonus(user_stats: Dict[str, Any]) -> int:
    """ユーザーレベルに応じたボーナス段階"""
    user_level = user_stats.get('user_level', 1)
    
    if user_level >= 50:
        return 2  # 超上級者
    elif user_level >= 25:
        return 1  # 上級者
    elif user_level >= 10:
        return 1  # 中級者
    else:
        return 0  # 初心者


def calculate_streak_bonus(learning_streak: int) -> int:
    """連続学習日数に応じたボーナス"""
    if learning_streak >= 30:
        return 2  # 1ヶ月連続
    elif learning_streak >= 14:
        return 1  # 2週間連続
    elif learning_streak >= 7:
        return 1  # 1週間連続
    else:
        return 0


def calculate_comprehension_bonus(avg_comprehension: float) -> int:
    """理解度平均に応じたボーナス"""
    if avg_comprehension >= 90:
        return 2  # 理解度90%以上
    elif avg_comprehension >= 80:
        return 1  # 理解度80%以上
    elif avg_comprehension >= 70:
        return 1  # 理解度70%以上
    else:
        return 0


def determine_special_effects(user_stats: Dict[str, Any], stage: int) -> Optional[str]:
    """特殊エフェクトを決定"""
    effects = []
    
    # 連続学習エフェクト
    streak = user_stats.get('learning_streak', 0)
    if streak >= 30:
        effects.append('✨ 学習マスター')
    elif streak >= 14:
        effects.append('🔥 継続の力')
    elif streak >= 7:
        effects.append('⭐ 頑張り屋')
    
    # レベルエフェクト
    level = user_stats.get('user_level', 1)
    if level >= 50:
        effects.append('👑 学習王')
    elif level >= 25:
        effects.append('🏆 学習達人')
    
    # 理解度エフェクト
    comprehension = user_stats.get('avg_comprehension_score', 0)
    if comprehension >= 95:
        effects.append('🧠 理解の達人')
    
    return '; '.join(effects) if effects else None


def calculate_size_bonus(user_stats: Dict[str, Any], stage: int) -> float:
    """学習データによる追加サイズボーナスを計算（健康度ベースサイズに上乗せ）"""
    base_size = 1.0
    
    # レベルボーナス
    level = user_stats.get('user_level', 1)
    level_bonus = min(0.2, level * 0.003)  # レベル100で+20%
    
    # 連続学習ボーナス
    streak = user_stats.get('learning_streak', 0)
    streak_bonus = min(0.15, streak * 0.003)  # 50日で+15%
    
    # 理解度ボーナス
    comprehension = user_stats.get('avg_comprehension_score', 0)
    comprehension_bonus = comprehension * 0.001  # 100%で+10%
    
    # 学習データによる追加ボーナスのみ（健康度ベースサイズは別途計算される）
    return base_size + level_bonus + streak_bonus + comprehension_bonus


def get_user_achievements(user_stats: Dict[str, Any]) -> list:
    """ユーザーの実績を取得"""
    achievements = []
    
    level = user_stats.get('user_level', 1)
    streak = user_stats.get('learning_streak', 0)
    videos_watched = user_stats.get('total_videos_watched', 0)
    comprehension = user_stats.get('avg_comprehension_score', 0)
    
    # レベル実績
    if level >= 100:
        achievements.append('🌟 レジェンド学習者')
    elif level >= 50:
        achievements.append('👑 学習マスター')
    elif level >= 25:
        achievements.append('🏆 学習エキスパート')
    elif level >= 10:
        achievements.append('⭐ 学習者')
    
    # 連続学習実績
    if streak >= 100:
        achievements.append('🔥 百日継続')
    elif streak >= 30:
        achievements.append('💪 一ヶ月継続')
    elif streak >= 7:
        achievements.append('⚡ 一週間継続')
    
    # 動画視聴実績
    if videos_watched >= 1000:
        achievements.append('📚 千本ノック')
    elif videos_watched >= 100:
        achievements.append('🎬 映画館マニア')
    elif videos_watched >= 50:
        achievements.append('📺 動画愛好家')
    
    # 理解度実績
    if comprehension >= 95:
        achievements.append('🧠 理解の天才')
    elif comprehension >= 90:
        achievements.append('💡 理解力抜群')
    elif comprehension >= 80:
        achievements.append('📖 理解上手')
    
    return achievements