# -*- coding: utf-8 -*-
"""
動的魚生成システム - SUPABASE連携版
ユーザーの学習データに基づいて魚を生成
"""
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import random
import io
import base64
import math
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional


class AdvancedFishGenerator:
    """SUPABASEデータ連携高度魚生成クラス"""
    
    def __init__(self):
        # 基本色パレット（学習パターン別）
        self.learning_style_colors = {
            "focused": {
                "primary": "#2E86AB",  # 深い青
                "secondary": "#A23B72",  # 深紫
                "accent": "#F18F01"  # オレンジ
            },
            "varied": {
                "primary": "#E63946",  # 赤
                "secondary": "#F77F00",  # オレンジ
                "accent": "#FCBF49"  # 黄色
            },
            "balanced": {
                "primary": "#2F9599",  # ティール
                "secondary": "#52734D",  # 緑
                "accent": "#DDDBF1"  # 薄紫
            }
        }
        
        # 理解度レベル別の魚の形状
        self.comprehension_shapes = {
            "easy": "round",    # 丸い、可愛らしい
            "medium": "normal", # 標準的な魚の形
            "hard": "sharp"     # 鋭い、高級感
        }
        
        # 学習頻度別のアニメーション速度
        self.frequency_animations = {
            "sporadic": 0.3,   # ゆっくり
            "regular": 0.6,    # 普通
            "intensive": 1.0   # 速い
        }
    
    def generate_personalized_fish(self, user_stats: Dict[str, Any], 
                                 user_patterns: Dict[str, Any],
                                 video_title: str = "",
                                 video_id: str = "",
                                 size: tuple = (120, 80)) -> Optional[str]:
        """ユーザーの学習データに基づいて個人化された魚を生成"""
        try:
            # ベース画像作成
            img = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # 学習パターンから色を決定
            learning_style = user_patterns.get("learning_style", "balanced")
            colors = self.learning_style_colors[learning_style]
            
            # エンゲージメントスコアに基づくサイズ調整
            engagement = user_stats.get("engagement_score", 0.5)
            scale = 0.7 + (engagement * 0.6)  # 0.7-1.3倍
            
            # 魚の基本形状を描画
            self._draw_fish_body(draw, size, colors, user_patterns, scale)
            
            # 理解度に基づく装飾追加
            self._add_comprehension_decorations(draw, size, user_stats, colors)
            
            # 学習ストリークに基づく特別効果
            self._add_streak_effects(img, user_patterns.get("learning_streaks", 0))
            
            # 時間帯に基づく背景効果
            self._add_time_based_effects(img, user_patterns.get("best_performance_time", "morning"))
            
            # Base64エンコード
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode()
            
        except Exception as e:
            print(f"魚生成エラー: {e}")
            return None
    
    def _draw_fish_body(self, draw: ImageDraw.Draw, size: tuple, colors: Dict, 
                       patterns: Dict, scale: float):
        """魚の本体を描画"""
        w, h = size
        center_x, center_y = w // 2, h // 2
        
        # サイズ調整
        body_width = int(w * 0.4 * scale)
        body_height = int(h * 0.6 * scale)
        
        # 理解度レベルに基づく形状
        difficulty = patterns.get("preferred_difficulty", "medium")
        
        if difficulty == "easy":
            # 丸い魚
            draw.ellipse([
                center_x - body_width, center_y - body_height//2,
                center_x + body_width//2, center_y + body_height//2
            ], fill=colors["primary"])
        elif difficulty == "hard":
            # 鋭い魚
            points = [
                (center_x - body_width, center_y),
                (center_x - body_width//2, center_y - body_height//2),
                (center_x + body_width//2, center_y - body_height//3),
                (center_x + body_width//2, center_y + body_height//3),
                (center_x - body_width//2, center_y + body_height//2)
            ]
            draw.polygon(points, fill=colors["primary"])
        else:
            # 標準的な魚
            draw.ellipse([
                center_x - body_width, center_y - body_height//2,
                center_x + body_width//2, center_y + body_height//2
            ], fill=colors["primary"])
        
        # 尻尾
        tail_points = [
            (center_x + body_width//2, center_y - body_height//4),
            (center_x + body_width, center_y),
            (center_x + body_width//2, center_y + body_height//4)
        ]
        draw.polygon(tail_points, fill=colors["secondary"])
        
        # 目
        eye_size = max(4, int(8 * scale))
        draw.ellipse([
            center_x - body_width//2 - eye_size, center_y - eye_size//2,
            center_x - body_width//2 + eye_size, center_y + eye_size//2
        ], fill='white')
        draw.ellipse([
            center_x - body_width//2 - eye_size//2, center_y - eye_size//4,
            center_x - body_width//2 + eye_size//2, center_y + eye_size//4
        ], fill='black')
    
    def _add_comprehension_decorations(self, draw: ImageDraw.Draw, size: tuple, 
                                     user_stats: Dict, colors: Dict):
        """理解度に基づく装飾を追加"""
        avg_comprehension = user_stats.get("avg_comprehension", 1.5)
        
        if avg_comprehension >= 2.5:  # 高理解度
            # 王冠のような装飾
            w, h = size
            center_x = w // 2
            crown_points = [
                (center_x - 15, h // 4),
                (center_x - 10, h // 6),
                (center_x - 5, h // 4 - 2),
                (center_x, h // 6 - 3),
                (center_x + 5, h // 4 - 2),
                (center_x + 10, h // 6),
                (center_x + 15, h // 4)
            ]
            draw.polygon(crown_points, fill=colors["accent"])
        elif avg_comprehension >= 2.0:  # 中理解度
            # シンプルな装飾
            w, h = size
            center_x = w // 2
            draw.polygon([
                (center_x - 8, h // 4),
                (center_x, h // 6),
                (center_x + 8, h // 4)
            ], fill=colors["accent"])
    
    def _add_streak_effects(self, img: Image.Image, streak_days: int):
        """学習ストリークに基づく特別効果"""
        if streak_days >= 7:  # 1週間以上の連続学習
            # 輝き効果
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.2)
            
            # 若干のブラー効果でオーラ感
            if streak_days >= 30:  # 1ヶ月以上
                blur = img.filter(ImageFilter.GaussianBlur(radius=1))
                img = Image.alpha_composite(blur, img)
    
    def _add_time_based_effects(self, img: Image.Image, best_time: str):
        """最適学習時間に基づく背景効果"""
        if best_time == "morning":
            # 朝の明るい効果
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)
        elif best_time == "night":
            # 夜の深い色調
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(0.8)
    
    def generate_evolution_fish(self, base_fish_stats: Dict, new_stats: Dict, 
                              video_title: str = "") -> Optional[str]:
        """既存の魚を進化させる"""
        # 成長度合いを計算
        old_engagement = base_fish_stats.get("engagement_score", 0.5)
        new_engagement = new_stats.get("engagement_score", 0.5)
        growth_factor = max(0.1, min(2.0, new_engagement / max(old_engagement, 0.1)))
        
        # サイズを大きく
        new_size = (int(120 * growth_factor), int(80 * growth_factor))
        return self.generate_personalized_fish(new_stats, {}, video_title, "", new_size)
    
    def generate_rare_fish(self, user_stats: Dict, achievement_type: str = "streak") -> Optional[str]:
        """特別な成果に基づくレア魚生成"""
        size = (150, 100)  # 大きめサイズ
        
        try:
            img = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            if achievement_type == "streak":
                # 連続学習記録達成
                colors = ["#FFD700", "#FFA500", "#FF6347"]  # ゴールド系
            elif achievement_type == "comprehension":
                # 高理解度達成
                colors = ["#9370DB", "#8A2BE2", "#4B0082"]  # 紫系
            elif achievement_type == "volume":
                # 大量学習達成
                colors = ["#00CED1", "#20B2AA", "#008B8B"]  # ティール系
            else:
                colors = ["#FF1493", "#FF69B4", "#FFB6C1"]  # ピンク系
            
            # レアな装飾付きの魚を描画
            self._draw_rare_fish_body(draw, size, colors)
            
            # 特別エフェクト
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.3)
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode()
            
        except Exception as e:
            print(f"レア魚生成エラー: {e}")
            return None
    
    def _draw_rare_fish_body(self, draw: ImageDraw.Draw, size: tuple, colors: List[str]):
        """レア魚の本体を描画"""
        w, h = size
        center_x, center_y = w // 2, h // 2
        
        # グラデーション風の多色魚体
        for i, color in enumerate(colors):
            offset = i * 3
            draw.ellipse([
                center_x - 50 + offset, center_y - 25 + offset,
                center_x + 30 - offset, center_y + 25 - offset
            ], fill=color)
        
        # 豪華な尻尾
        tail_colors = colors[::-1]  # 逆順
        for i, color in enumerate(tail_colors):
            offset = i * 2
            tail_points = [
                (center_x + 30 - offset, center_y - 15 + offset),
                (center_x + 60 + i*5, center_y),
                (center_x + 30 - offset, center_y + 15 - offset)
            ]
            draw.polygon(tail_points, fill=color)
        
        # 特別な目
        draw.ellipse([center_x - 35, center_y - 8, center_x - 20, center_y + 8], fill='white')
        draw.ellipse([center_x - 32, center_y - 5, center_x - 23, center_y + 5], fill='black')
        draw.ellipse([center_x - 29, center_y - 2, center_x - 26, center_y + 2], fill='white')  # ハイライト
    
    def calculate_fish_rank(self, user_stats: Dict, all_users_stats: List[Dict]) -> Tuple[str, int]:
        """ユーザーの相対的なランクを計算"""
        if not all_users_stats:
            return "初心者", 1
        
        user_engagement = user_stats.get("engagement_score", 0.0)
        
        # 全ユーザーの中での順位を計算
        sorted_users = sorted(all_users_stats, key=lambda x: x.get("engagement_score", 0.0), reverse=True)
        user_rank = len(sorted_users)
        
        for i, stats in enumerate(sorted_users):
            if stats.get("engagement_score", 0.0) <= user_engagement:
                user_rank = i + 1
                break
        
        total_users = len(sorted_users)
        percentile = (user_rank / total_users) * 100
        
        if percentile <= 10:
            return "マスター", user_rank
        elif percentile <= 25:
            return "エキスパート", user_rank
        elif percentile <= 50:
            return "上級者", user_rank
        elif percentile <= 75:
            return "中級者", user_rank
        else:
            return "初心者", user_rank


class DynamicFishGenerator(AdvancedFishGenerator):
    """後方互換性のための従来クラス"""
    
    def generate_simple_fish(self, title: str, size: tuple = (100, 60)) -> str:
        """シンプルな魚画像を生成（従来互換）"""
        # 基本的な魚生成
        return self.generate_personalized_fish(
            {"engagement_score": 0.5}, 
            {"learning_style": "balanced"}, 
            title, "", size
        ) or ""