# -*- coding: utf-8 -*-
"""
アニメーション水槽のコンポーネント
"""
import streamlit as st
import streamlit.components.v1
import random
from datetime import datetime
from PIL import Image, ImageChops
from typing import cast, Dict, Any
from sqlmodel import select
from .db import get_session
from .models import Fish
from .forgetting import update_fish_state


def weight_to_stage(weight: int) -> int:
    """Convert weight in grams to a stage 1..5.

    Thresholds chosen to map previous weight ranges into five visual stages.
    """
    if weight is None:
        return 1
    try:
        w = int(weight)
    except Exception:
        return 1
    if w <= 70:
        return 1
    if w <= 100:
        return 2
    if w <= 140:
        return 3
    if w <= 180:
        return 4
    return 5

# 健康度から段階とラベルを自動計算
def get_stage_from_health(health: float) -> tuple[int, str]:
    """
    健康度（0-100）から段階（1-5）とラベルを計算
    
    Args:
        health: 健康度（0-100%）
        
    Returns:
        tuple: (stage, label)
    """
    if health <= 0:
        return (1, '💀 死亡')
    elif health < 20:
        return (1, '💔 衰弱')
    elif health < 40:
        return (2, '😰 弱っている')
    elif health < 60:
        return (3, '😐 普通')
    elif health < 80:
        return (4, '😊 元気')
    else:
        return (5, '🤩 絶好調')


def get_video_statistics(video_id: int) -> dict:
    """
    動画の視聴統計情報を取得
    
    Args:
        video_id: 動画ID
        
    Returns:
        dict: 統計情報（view_count, estimated_watch_time, comprehension_score）
    """
    try:
        # 基本統計の取得
        with get_session() as ses:
            from .models import View, Video
            from sqlmodel import func
            
            # 視聴回数（Viewテーブルから取得）
            views = ses.exec(select(View).where(View.video_id == video_id)).all()
            view_count = len(views)
            
            # 動画情報と魚の状態取得
            video = ses.exec(select(Video).where(Video.id == video_id)).first()
            fish = ses.exec(select(Fish).where(Fish.video_id == video_id)).first()
            
            # 推定視聴時間（視聴回数 × 推定動画時間）
            estimated_duration_minutes = 10  # デフォルト10分
            
            # 実際の視聴時間データがある場合は使用
            total_duration_seconds = sum(
                v.duration_sec for v in views if v.duration_sec is not None
            )
            
            if total_duration_seconds and total_duration_seconds > 0:
                total_watch_time = int(total_duration_seconds / 60)  # 分に変換
            else:
                total_watch_time = view_count * estimated_duration_minutes
            
            # 理解度スコア計算
            if fish:
                # 健康度ベースの理解度計算
                base_comprehension = fish.health * 0.8  # 健康度の80%をベース
                
                # 視聴回数によるボーナス（多く見るほど理解度向上）
                engagement_bonus = min(20, view_count * 3)  # 最大20%のボーナス
                
                comprehension_score = min(100, base_comprehension + engagement_bonus)
            else:
                comprehension_score = 50  # デフォルト50%
            
            # 理解度記録がある場合は平均を使用
            comprehension_records = [v.comprehension for v in views if v.comprehension is not None]
            
            if comprehension_records:
                avg_comprehension = sum(comprehension_records) / len(comprehension_records)
                # 1-3スケールを0-100%に変換
                recorded_comprehension = (avg_comprehension - 1) * 50  # 1→0%, 2→50%, 3→100%
                # 計算値と記録值の平均を取る
                comprehension_score = (comprehension_score + recorded_comprehension) / 2
        
        return {
            'view_count': view_count,
            'total_watch_time_minutes': total_watch_time,
            'comprehension_score': round(comprehension_score, 1),
            'engagement_level': min(5, view_count // 2 + 1)  # 1-5のエンゲージメントレベル
        }
    
    except Exception as e:
        # エラー時はデフォルト値を返す
        return {
            'view_count': 0,
            'total_watch_time_minutes': 0,
            'comprehension_score': 50.0,
            'engagement_level': 1
        }

# 後方互換性のため残しておく（廃止予定）
HEALTH_STAGE_LABELS = {
    1: '衰弱',
    2: '弱い', 
    3: '普通',
    4: '元気',
    5: '絶好調',
}


def render_animated_tank():
    """アニメーション水槽を描画する"""
    st.subheader("🐠 金魚の水槽 - ライブアニメーション")

    # パッシブ減衰の自動適用: 水槽を表示する際に、「当日未適用」の魚だけ一度更新する
    try:
        today_utc = datetime.utcnow().date()
        updated_count = 0
        with get_session() as ses:
            from .models import View
            fishes = ses.exec(select(Fish)).all()
            for f in fishes:
                # last_update が今日でなければ、今日分の自然減衰を適用して DB 更新
                if (f.last_update is None) or (f.last_update.date() < today_utc):
                    # 該当動画の視聴回数を取得して view_count を渡す
                    view_count = 0
                    try:
                        if f.video_id:
                            views = ses.exec(select(View).where(View.video_id == f.video_id)).all()
                            view_count = len(views)
                    except Exception:
                        view_count = 0
                    update_fish_state(f, datetime.utcnow(), reviewed_today=False, view_count=view_count)
                    ses.add(f)
                    updated_count += 1
            if updated_count > 0:
                ses.commit()
        if updated_count > 0:
            st.info(f"自然減衰を {updated_count} 匹の金魚に適用しました（本日1回）。")
    except Exception as e:
        # 何らかの例外が起きても描画は続けるがログを出す
        st.warning(f"自動自然減衰の適用中にエラーが発生しました: {e}")

    # アニメーション制御
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        animation_speed = st.slider("泳ぐ速度", 0.1, 2.0, 1.0, 0.1)
    with col2:
        show_bubbles = st.checkbox("泡を表示", value=True)
    with col3:
        show_decorations = st.checkbox("水草・装飾を表示", value=True)
    with col4:
        # 高度な魚生成はログイン時に自動で有効にする（チェックボックスを廃止）
        show_advanced_fish = st.session_state.get('logged_in', False)
    # NOTE: こってぃくんBIT画像は常時使用する仕様に変更
    
    with get_session() as ses:
        from .models import Video, View
        fishes = ses.exec(select(Fish)).all()
        
        # 金魚とビデオのペアを作成（視聴回数を含める）
        fish_video_pairs = []
        for fish in fishes:
            video = ses.exec(select(Video).where(Video.id == fish.video_id)).first()
            view_count = 0
            if video:
                try:
                    views = ses.exec(select(View).where(View.video_id == video.id)).all()
                    view_count = len(views)
                except Exception:
                    view_count = 0
            fish_video_pairs.append((fish, video, view_count))

    # 高度な魚生成を使用する場合
    advanced_fish_data = []
    if st.session_state.get('logged_in', False):
        try:
            from .dynamic_fish_generator import AdvancedFishGenerator, DynamicFishGenerator
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from repositories.supabase_repo import get_user_stats, get_user_learning_patterns, get_all_users_stats
            
            # 現在のユーザー情報を取得
            user = st.session_state.get('user')
            if user and user.get('id'):
                user_id = user['id']
                
                # SUPABASEから学習データを取得
                user_stats = get_user_stats(user_id)
                learning_patterns = get_user_learning_patterns(user_id)
                all_users_stats = get_all_users_stats()
                
                # 高度な魚生成器を初期化
                advanced_generator = AdvancedFishGenerator()
                dynamic_generator = DynamicFishGenerator()
                
                # 既存の魚に加えて、学習データベース魚を表示
                for i, (fish, video) in enumerate(fish_video_pairs):
                    if video:
                        # 動的魚生成（引数は学習統計データ、学習パターンデータ、動画タイトル）
                        fish_image = advanced_generator.generate_personalized_fish(
                            user_stats, learning_patterns, video.title
                        )
                        
                        # 進化魚の生成を試行
                        evolution_fish = advanced_generator.generate_evolution_fish(
                            {"memory_strength": fish.memory_strength},
                            user_stats
                        )
                        
                        # レア魚の生成を試行
                        rare_fish = advanced_generator.generate_rare_fish(user_stats)
                        
                        # レア度を計算（学習継続日数ベース）
                        streak_days = user_stats.get("streak_days", 0)
                        rarity_level = min(streak_days / 100.0, 1.0)  # 100日で最高レア度
                        evolution_stage = min(user_stats.get("total_videos", 0) / 50.0, 5.0)  # 50動画で最大進化
                        
                        advanced_fish_data.append({
                            'fish': fish,
                            'video': video,
                            'fish_image': fish_image,
                            'evolution_fish': evolution_fish,
                            'rare_fish': rare_fish,
                            'evolution_stage': evolution_stage,
                            'rarity_level': rarity_level,
                            'is_legendary': rarity_level >= 0.9
                        })
                
                # 進化・レア魚情報を表示
                if advanced_fish_data:
                    avg_evolution = sum(f['evolution_stage'] for f in advanced_fish_data) / len(advanced_fish_data)
                    st.info(f"🌟 学習進捗による魚の進化情報 | 平均進化段階: {avg_evolution:.1f}/5.0")
                    
                    # レジェンド魚の存在チェック
                    legendary_fish = [f for f in advanced_fish_data if f['is_legendary']]
                    if legendary_fish:
                        st.success(f"✨ 伝説の魚が {len(legendary_fish)} 匹泳いでいます！")
                        
        except Exception as e:
            st.warning(f"高度な魚生成でエラー: {str(e)}")
            advanced_fish_data = []

    # 金魚がいない場合の表示
    if not fish_video_pairs:
        empty_tank_html = """
        <style>
        .empty-tank {
            width: 100%;
            height: 520px;
            background: linear-gradient(180deg, #87CEEB 0%, #4682B4 50%, #1E90FF 100%);
            border: 8px solid #8B4513;
            border-radius: 20px;
            position: relative;
            overflow: hidden;
            box-shadow: inset 0 0 50px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .empty-message {
            font-size: 24px;
            color: rgba(255,255,255,0.8);
            text-align: center;
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 15px;
        }
        .water-plants {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: linear-gradient(0deg, #228B22 0%, #32CD32 100%);
            clip-path: polygon(0 100%, 10% 70%, 20% 90%, 30% 60%, 40% 80%, 50% 50%, 60% 75%, 70% 55%, 80% 85%, 90% 65%, 100% 100%);
        }
        .pebbles {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 20px;
            background: radial-gradient(circle, #A0522D 20%, #8B4513 40%, #654321 60%);
        }
        </style>
        <div class="empty-tank">
            <div class="pebbles"></div>
            <div class="water-plants"></div>
            <div class="empty-message">
                🐠 水槽は空です<br>
                動画を追加して金魚を飼いましょう！
            </div>
        </div>
        """
        streamlit.components.v1.html(empty_tank_html, height=550)
        return

    # CSS アニメーションを使用した金魚水槽
    tank_html = f"""
    <style>
    .tank-container {{
        width: 100%;
        height: 520px;
        background: linear-gradient(180deg, #87CEEB 0%, #4682B4 50%, #1E90FF 100%);
        border: 8px solid #8B4513;
        border-radius: 20px;
        position: relative;
        overflow: hidden;
        box-shadow: inset 0 0 50px rgba(0,0,0,0.3);
    }}
    
    .fish {{
        position: absolute;
        animation: swim linear infinite;
        filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.3));
        transition: all 0.3s ease;
        cursor: pointer;
        user-select: none;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    
    .custom-fish {{
        transition: all 0.3s ease;
    }}
    
    .fish:hover {{
        transform: scale(1.3) !important;
        filter: drop-shadow(4px 4px 8px rgba(0,0,0,0.5));
        z-index: 10;
    }}
    
    .fish:hover .custom-fish {{
        filter: brightness(1.2);
    }}
    
    @keyframes swim {{
        0% {{ 
            transform: translateX(-100px) scaleX(1); 
        }}
        25% {{ 
            transform: translateX(calc(80vw - 200px)) translateY(-30px) scaleX(1); 
        }}
        50% {{ 
            transform: translateX(calc(80vw - 100px)) translateY(30px) scaleX(-1); 
        }}
        75% {{ 
            transform: translateX(100px) translateY(-20px) scaleX(-1); 
        }}
        100% {{ 
            transform: translateX(-100px) scaleX(1); 
        }}
    }}
    
    @keyframes swim-legendary {{
        0% {{ 
            transform: translateX(-100px) scaleX(1) translateY(0px); 
        }}
        15% {{ 
            transform: translateX(calc(20vw)) translateY(-40px) scaleX(1) rotate(15deg); 
        }}
        35% {{ 
            transform: translateX(calc(50vw - 150px)) translateY(-20px) scaleX(1) rotate(-10deg); 
        }}
        50% {{ 
            transform: translateX(calc(80vw - 100px)) translateY(40px) scaleX(-1) rotate(5deg); 
        }}
        65% {{ 
            transform: translateX(calc(60vw)) translateY(10px) scaleX(-1) rotate(-15deg); 
        }}
        85% {{ 
            transform: translateX(100px) translateY(-30px) scaleX(-1) rotate(10deg); 
        }}
        100% {{ 
            transform: translateX(-100px) scaleX(1) translateY(0px); 
        }}
    }}
    
    @keyframes glow-legendary {{
        0% {{ 
            filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.3)) drop-shadow(0 0 10px rgba(255,215,0,0.6)); 
        }}
        100% {{ 
            filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.3)) drop-shadow(0 0 20px rgba(255,215,0,0.9)); 
        }}
    }}
    
    .bubble {{
        position: absolute;
        background: rgba(255,255,255,0.7);
        border-radius: 50%;
        animation: float linear infinite;
        box-shadow: inset 0 0 10px rgba(255,255,255,0.5);
    }}
    
    @keyframes float {{
        0% {{ 
            transform: translateY(520px) scale(0); 
            opacity: 0; 
        }}
        10% {{ 
            opacity: 1; 
        }}
        90% {{ 
            opacity: 0.8; 
        }}
        100% {{ 
            transform: translateY(-50px) scale(1.5); 
            opacity: 0; 
        }}
    }}
    
    .water-plants {{
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 80px;
        background: linear-gradient(0deg, #1B5E20 0%, #2E7D32 50%, #4CAF50 100%);
        clip-path: polygon(0 100%, 8% 60%, 15% 85%, 25% 45%, 35% 75%, 45% 40%, 55% 70%, 65% 35%, 75% 80%, 85% 50%, 92% 75%, 100% 100%);
        animation: sway 6s ease-in-out infinite;
        z-index: 1;
    }}
    
    .seaweed {{
        position: absolute;
        bottom: 0;
        width: 8px;
        background: linear-gradient(0deg, #1B5E20 0%, #388E3C 50%, #66BB6A 100%);
        border-radius: 4px;
        transform-origin: bottom center;
        animation: seaweed-sway ease-in-out infinite;
    }}
    
    .seaweed-1 {{
        left: 15%;
        height: 120px;
        animation-duration: 4s;
        animation-delay: 0s;
    }}
    
    .seaweed-2 {{
        left: 25%;
        height: 100px;
        animation-duration: 5s;
        animation-delay: 1s;
    }}
    
    .seaweed-3 {{
        left: 70%;
        height: 140px;
        animation-duration: 4.5s;
        animation-delay: 2s;
    }}
    
    .seaweed-4 {{
        left: 85%;
        height: 90px;
        animation-duration: 3.5s;
        animation-delay: 0.5s;
    }}
    
    .coral {{
        position: absolute;
        bottom: 20px;
        border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
        animation: coral-pulse 8s ease-in-out infinite;
    }}
    
    .coral-1 {{
        left: 10%;
        width: 30px;
        height: 40px;
        background: linear-gradient(45deg, #FF6B6B, #FF8E8E);
        animation-delay: 0s;
    }}
    
    .coral-2 {{
        right: 15%;
        width: 25px;
        height: 35px;
        background: linear-gradient(45deg, #4ECDC4, #7ED7D1);
        animation-delay: 2s;
    }}
    
    .coral-3 {{
        left: 40%;
        width: 20px;
        height: 30px;
        background: linear-gradient(45deg, #FFE066, #FFEB99);
        animation-delay: 4s;
    }}
    
    .rocks {{
        position: absolute;
        bottom: 0;
        border-radius: 50% 50% 0 0;
        background: linear-gradient(45deg, #8D6E63, #A1887F);
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
    }}
    
    .rock-1 {{
        left: 5%;
        width: 40px;
        height: 20px;
    }}
    
    .rock-2 {{
        right: 20%;
        width: 35px;
        height: 25px;
    }}
    
    .rock-3 {{
        left: 60%;
        width: 30px;
        height: 15px;
    }}
    
    @keyframes sway {{
        0%, 100% {{ transform: translateX(0) scaleY(1); }}
        25% {{ transform: translateX(3px) scaleY(1.02); }}
        50% {{ transform: translateX(-2px) scaleY(0.98); }}
        75% {{ transform: translateX(2px) scaleY(1.01); }}
    }}
    
    @keyframes seaweed-sway {{
        0%, 100% {{ transform: rotate(0deg) scaleX(1); }}
        25% {{ transform: rotate(3deg) scaleX(1.05); }}
        50% {{ transform: rotate(-2deg) scaleX(0.95); }}
        75% {{ transform: rotate(4deg) scaleX(1.02); }}
    }}
    
    @keyframes coral-pulse {{
        0%, 100% {{ transform: scale(1); opacity: 0.8; }}
        50% {{ transform: scale(1.1); opacity: 1; }}
    }}
    
    .particles {{
        position: absolute;
        width: 2px;
        height: 2px;
        background: rgba(255, 255, 255, 0.6);
        border-radius: 50%;
        animation: drift linear infinite;
    }}
    
    @keyframes drift {{
        0% {{ 
            transform: translateY(520px) translateX(0px) scale(0.5); 
            opacity: 0; 
        }}
        10% {{ 
            opacity: 1; 
        }}
        90% {{ 
            opacity: 0.8; 
        }}
        100% {{ 
            transform: translateY(-50px) translateX(50px) scale(1); 
            opacity: 0; 
        }}
    }}
    }}
    
    .pebbles {{
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 20px;
        background: radial-gradient(circle, #A0522D 20%, #8B4513 40%, #654321 60%);
    }}
    
    .fish-name {{
        position: absolute;
        background: rgba(0,0,0,0.7);
        color: white;
        padding: 2px 6px;
        border-radius: 8px;
        font-size: 10px;
        font-family: Arial, sans-serif;
        transform: translateX(-50%);
        white-space: nowrap;
        opacity: 0;
        transition: opacity 0.3s ease;
        z-index: 20;
    }}
    
    .fish:hover .fish-name {{
        opacity: 1;
    }}
    </style>
    
    <div class="tank-container">
        <!-- 水槽の底の装飾 -->
        <div class="pebbles"></div>
        
        """ + (f"""
        <!-- メインの水草（背景） -->
        <div class="water-plants"></div>
        
        <!-- 個別の海藻 -->
        <div class="seaweed seaweed-1"></div>
        <div class="seaweed seaweed-2"></div>
        <div class="seaweed seaweed-3"></div>
        <div class="seaweed seaweed-4"></div>
        
        <!-- 珊瑚 -->
        <div class="coral coral-1"></div>
        <div class="coral coral-2"></div>
        <div class="coral coral-3"></div>
        
        <!-- 岩 -->
        <div class="rocks rock-1"></div>
        <div class="rocks rock-2"></div>
        <div class="rocks rock-3"></div>
        """ if show_decorations else "") + """
    """

    # 金魚を追加
    # advanced_fish_data があればそれを表示、なければ事前に作成した (fish, video, view_count) のペアを使う
    display_data = advanced_fish_data if advanced_fish_data else fish_video_pairs
    # こってぃくんBIT の画像を読み込む（存在すれば） — 常時読み込み
    kotti_images = {}
    try:
        import os, base64, io
        # プロジェクトルート直下のフォルダを想定
        kotti_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'こってぃくんBIT')
        expected = [
            ('normal', '①ノーマル.jpg'),
            ('cry', '②泣く.png'),
            ('smile', '③笑う.png'),
            ('sparkle', '④きらきら.png'),
            ('legend', '⑤伝説.png'),
        ]

        # Use the original files from the 'こってぃくんBIT' folder as-is.
        # We base64-encode the original file bytes and set the correct MIME type
        # so the <img> tag can display them directly. This avoids using the
        # previously trimmed/processed PNGs for display.
        for key, fname in expected:
            path = os.path.join(kotti_dir, fname)
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        raw = f.read()
                    ext = path.lower().rsplit('.', 1)[-1]
                    if ext in ('png', 'apng'):
                        mime = 'image/png'
                    elif ext in ('jpg', 'jpeg'):
                        mime = 'image/jpeg'
                    else:
                        mime = 'application/octet-stream'
                    b64 = base64.b64encode(raw).decode('ascii')
                    kotti_images[key] = f"data:{mime};base64,{b64}"
                except Exception as ee:
                    st.warning(f"個別画像の読み込みでエラー ({fname}): {ee}")
    except Exception as e:
        st.warning(f"こってぃくんBIT画像の読み込みでエラー: {e}")
    
    for i, item in enumerate(display_data):
        # item は dict（高度な魚データ）または tuple (fish, video, view_count)
        if isinstance(item, dict):
            f = item['fish']
            video = item['video']
            evolution_stage = item.get('evolution_stage', 1.0)
            rarity_level = item.get('rarity_level', 0.0)
            is_legendary = item.get('is_legendary', False)
            view_count = item.get('view_count', 0)
        else:
            f, video, view_count = item
            evolution_stage = 1.0
            rarity_level = 0.0
            is_legendary = False

        # 健康度から段階とラベルを自動計算
        stage, stage_label = get_stage_from_health(f.health)
        
        # Supabaseユーザーデータがある場合は拡張ロジックを適用
        special_effects = None
        size_bonus = 1.0
        user_achievements = []
        
        if st.session_state.get('user_id'):
            try:
                from .enhanced_kotti_logic_fixed import get_enhanced_kotti_state
                # video_idをintに変換、取得できない場合はNoneのまま
                video_id = None
                if hasattr(video, 'id') and video.id:
                    try:
                        video_id = int(video.id)
                    except (ValueError, TypeError):
                        video_id = None
                
                enhanced_state = get_enhanced_kotti_state(
                    st.session_state['user_id'], 
                    video_id,
                    stage  # 健康度ベースのstageを渡す
                )
                # 健康度ベースのstageを維持し、特殊効果のみ取得
                special_effects = enhanced_state.get('special_effects')
                size_bonus = enhanced_state.get('bonus_size', 1.0)
                user_achievements = enhanced_state.get('achievements', [])
                
                # 実績表示
                if user_achievements:
                    st.sidebar.success(f"🏆 {video.title}の実績:")
                    for achievement in user_achievements:
                        st.sidebar.caption(achievement)
                        
            except Exception as e:
                # エラー時はデフォルト値を維持
                pass

        # サイズ計算（進化段階に基づくボーナス） — stage を元に大きさを決める
        # stage 1..5 を 0.6..2.0 の範囲にマップ
        base_size_factor = 0.6 + (stage - 1) * (1.4 / 4)
        evolution_bonus = 1.0 + (evolution_stage - 1.0) * 0.3  # 進化で30%ずつ大きく
        
        # Supabaseからのサイズボーナスを適用
        enhanced_size_bonus = size_bonus if 'size_bonus' in locals() else 1.0
        
        size_factor = base_size_factor * evolution_bonus * enhanced_size_bonus
        font_size = int(25 * size_factor)
        
        # 透明度計算（健康度とレア度に基づく）
        base_opacity = max(0.6, min(1.0, f.health / 100))
        rarity_bonus = rarity_level * 0.2  # レア度で最大20%透明度アップ
        opacity = min(1.0, base_opacity + rarity_bonus)
        
        # 泳ぐ速度（健康度と進化段階に基づく）
        base_speed = max(0.5, f.health / 100)
        evolution_speed_bonus = evolution_stage * 0.1  # 進化で10%ずつ速く
        swim_speed = base_speed * (1.0 + evolution_speed_bonus)
        swim_duration = max(6, int(15 / swim_speed)) / animation_speed
        
        # レジェンド魚の特殊エフェクト
        css_special_effects = ""
        if is_legendary:
            css_special_effects = f"""
            animation: swim-legendary {swim_duration}s linear infinite, glow-legendary 2s ease-in-out infinite alternate;
            """
        
        # Supabaseからの特殊エフェクト表示（サイドバーに）
        if 'special_effects' in locals() and special_effects and i == 0:  # 最初の魚にのみ表示
            st.sidebar.info(f"🎉 特殊効果:             {css_special_effects}")
        
        # 高さの位置をランダムに（魚のIDに基づいて一定）
        random.seed(f.id)  # 一定の位置を保つため
        top_position = random.randint(60, 350)
        
        # アニメーション遅延（魚ごとに異なるタイミング）
        delay = (i * 3) % 12
        
        # 動画タイトルを短縮
        short_title = video.title[:20] + "..." if len(video.title) > 20 else video.title
        
        # 色に基づいて異なる魚の絵文字を選択
        fish_emojis = {
            "#FF6B6B": "🐡",   # 赤 - フグ
            "#4ECDC4": "🐠",   # シアン - 魚
            "#45B7D1": "🐟",   # 青 - 熱帯魚
            "#96CEB4": "🦈",   # 緑 - サメ
            "#FFEAA7": "🐡",   # 黄色 - フグ
            "#DDA0DD": "🐙",   # プラム - タコ
            "#FFA07A": "🦐",   # サーモン - エビ
            "#98D8C8": "🐠",   # ミントグリーン - 魚
            "#F7DC6F": "🐡",   # レモン - フグ
            "#BB8FCE": "🐙"    # 薄紫 - タコ
        }
        fish_emoji = fish_emojis.get(f.fish_color, "🐠")
        
        # 画像ソースを決定: こってぃくんBIT優先、健康度ベースで選択
        img_src = None
        if kotti_images:
            # 優先ルール: レジェンド優先、その後は健康度(health)に合わせた固定マッピング
            if is_legendary and 'legend' in kotti_images:
                img_src = kotti_images['legend']
            else:
                # 健康度に基づく画像選択（健康度が低いほど悲しい画像）
                health_to_key = {
                    1: 'cry',      # 0-20%: 死亡・衰弱
                    2: 'cry',      # 20-40%: 弱っている  
                    3: 'normal',   # 40-60%: 普通
                    4: 'smile',    # 60-80%: 元気
                    5: 'sparkle',  # 80-100%: 絶好調
                }
                preferred = health_to_key.get(stage, 'normal')
                if preferred in kotti_images:
                    img_src = kotti_images[preferred]
                else:
                    # フォールバック: 健康度に基づく確率的選択
                    choices = []
                    health_ratio = f.health / 100.0
                    choices += ['cry'] * max(1, int(30 * (1.0 - health_ratio)))  # 健康度が低いほどcry多め
                    choices += ['normal'] * 40
                    choices += ['smile'] * max(1, int(20 * health_ratio))        # 健康度が高いほどsmile多め
                    choices += ['sparkle'] * max(1, int(10 * health_ratio))      # 健康度が高いほどsparkle多め
                    sel = random.choice(choices)
                    if sel in kotti_images:
                        img_src = kotti_images[sel]

        # HTMLブロック（画像があれば画像タグ、なければ既存の絵文字表示）
        if img_src:
            # Move opacity to the image itself so the background of the image container
            # stays opaque and doesn't let the tank's blue background show through.
            tank_html += f'''
        <div class="fish" style="
            top: {top_position}px;
            animation-duration: {swim_duration}s;
            animation-delay: {delay}s;
            transform: scale({size_factor});
            {special_effects if special_effects else f'animation: swim {swim_duration}s linear infinite;'}
        ">
            <div style="width:{int(80*size_factor)}px; height:{int(40*size_factor)}px; display:flex; align-items:center; justify-content:center;">
                <img src="{img_src}" style="width:100%; height:100%; object-fit:contain; opacity:{opacity}; display:block; background:transparent;"/>
            </div>
                <div class="fish-name" style="top: -35px; left: 50%; color: {f.fish_color};">
                {short_title}<br>
                💚{f.health:.0f}%
                {'🌟' + str(round(evolution_stage, 1)) if evolution_stage > 1.0 else ''}
                {'👑' if is_legendary else ''}
            </div>
        </div>
        '''
        else:
            # For emoji-based fallback, apply opacity only to the emoji element so
            # the surrounding decoration (like name labels) remains readable and
            # the tank background doesn't bleed through.
            tank_html += f"""
        <div class="fish" style="
            top: {top_position}px;
            animation-duration: {swim_duration}s;
            animation-delay: {delay}s;
            transform: scale({size_factor});
            font-size: 40px;
            text-shadow: 0 0 20px {f.fish_color}, 0 0 30px {f.fish_color}, 0 0 40px {f.fish_color};
            {'filter: drop-shadow(0 0 10px ' + f.fish_color + ');' if not is_legendary else ''}
            {special_effects if special_effects else f'animation: swim {swim_duration}s linear infinite;'}
        ">
            <span style="display:inline-block; opacity:{opacity};">{fish_emoji}{'✨' if is_legendary else ''}</span>
            <div class="fish-name" style="top: -35px; left: 50%; color: {f.fish_color};">
                {short_title}<br>
                💚{f.health:.0f}%
                {'🌟' + str(round(evolution_stage, 1)) if evolution_stage > 1.0 else ''}
                {'👑' if is_legendary else ''}
            </div>
        </div>
        """

    # 泡のアニメーション
    if show_bubbles:
        for i in range(12):
            bubble_size = random.randint(4, 12)
            bubble_left = random.randint(5, 95)
            bubble_duration = random.randint(4, 8)
            bubble_delay = random.uniform(0, 6)
            
            tank_html += f"""
            <div class="bubble" style="
                width: {bubble_size}px;
                height: {bubble_size}px;
                left: {bubble_left}%;
                animation-duration: {bubble_duration}s;
                animation-delay: {bubble_delay}s;
            "></div>
            """

    # 水中のパーティクル（小さな粒子）を追加
    for i in range(15):
        particle_left = random.randint(0, 100)
        particle_duration = random.randint(8, 15)
        particle_delay = random.uniform(0, 10)
        
        tank_html += f"""
        <div class="particles" style="
            left: {particle_left}%;
            animation-duration: {particle_duration}s;
            animation-delay: {particle_delay}s;
        "></div>
        """

    tank_html += "</div>"
    
    # HTMLをレンダリング
    streamlit.components.v1.html(tank_html, height=550)
    
    # 金魚の情報表示
    st.markdown("### 🐠 水槽の住人たち")
    
    # 高度な魚データがある場合は拡張情報を表示
    if advanced_fish_data:
        # 統計情報の表示
        st.markdown("#### 🌟 学習進化統計")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_evolution = sum(f['evolution_stage'] for f in advanced_fish_data) / len(advanced_fish_data)
            st.metric("平均進化段階", f"{avg_evolution:.1f}/5.0")
        
        with col2:
            avg_rarity = sum(f['rarity_level'] for f in advanced_fish_data) / len(advanced_fish_data)
            st.metric("平均レア度", f"{avg_rarity:.2f}")
        
        with col3:
            legendary_count = sum(1 for f in advanced_fish_data if f['is_legendary'])
            st.metric("伝説魚の数", f"{legendary_count}匹")
        
        with col4:
            total_fish = len(advanced_fish_data)
            st.metric("総魚数", f"{total_fish}匹")
    
    # 個別魚の情報表示
    # advanced_fish_data があればそれを表示、なければ (fish, video, view_count) のペアを使う
    display_pairs = advanced_fish_data if advanced_fish_data else fish_video_pairs
    cols = st.columns(min(4, len(display_pairs)))
    
    for i, item in enumerate(display_pairs):
        # item may be a dict (advanced_fish_data entries) or a tuple (fish, video, view_count)
        if isinstance(item, dict):
            d = cast(Dict[str, Any], item)
            fish = d['fish']
            video = d['video']
            evolution_stage = d.get('evolution_stage', 1.0)
            rarity_level = d.get('rarity_level', 0.0)
            is_legendary = d.get('is_legendary', False)
            view_count = d.get('view_count', 0)
        else:
            fish, video, view_count = item
            evolution_stage = 1.0
            rarity_level = 0.0
            is_legendary = False
        with cols[i % len(cols)]:
            # 健康度から段階とラベルを統一的に取得
            stage_i, stage_label_i = get_stage_from_health(fish.health)
            health_emoji = "💚" if fish.health > 70 else "💛" if fish.health > 40 else "❤️"
            weight_emoji = "🐋" if fish.weight_g > 150 else "🐟" if fish.weight_g > 75 else "🐠"

            # 最後の更新からの日数
            if fish.last_update:
                days_ago = (datetime.utcnow() - fish.last_update).days
                last_view_text = f"{days_ago}日前" if days_ago > 0 else "今日"
            else:
                last_view_text = "未更新"
            
            # 拡張情報の表示
            title_suffix = ""
            
            if evolution_stage > 1.0:
                title_suffix += f" 🌟{evolution_stage:.1f}"
            
            if is_legendary:
                title_suffix += " 👑"
            elif rarity_level > 0.5:
                title_suffix += " ⭐"
            
            # メイン健康度表示
            st.metric(
                f"{health_emoji} {video.title[:15]}...{title_suffix}",
                f"健康度: {fish.health:.1f}%"
            )
            
            # 進捗バロメーター表示（3カラムレイアウト）
            st.markdown("**📊 学習進捗**")
            prog_col1, prog_col2, prog_col3 = st.columns(3)
            
            try:
                stats = get_video_statistics(video.id)
                
                with prog_col1:
                    st.metric(
                        "📺 視聴回数",
                        f"{stats['view_count']}回",
                        delta="エンゲージメント" if stats['view_count'] > 0 else "未視聴"
                    )
                
                with prog_col2:
                    watch_hours = stats['total_watch_time_minutes'] / 60
                    if watch_hours >= 1:
                        time_display = f"{watch_hours:.1f}時間"
                    else:
                        time_display = f"{stats['total_watch_time_minutes']}分"
                    
                    st.metric(
                        "⏱️ 視聴時間",
                        time_display,
                        delta="学習投資"
                    )
                
                with prog_col3:
                    comprehension_emoji = "🎓" if stats['comprehension_score'] >= 80 else "📖" if stats['comprehension_score'] >= 60 else "📚"
                    st.metric(
                        f"{comprehension_emoji} 理解度",
                        f"{stats['comprehension_score']:.0f}%",
                        delta="習得レベル"
                    )
                    
            except Exception as e:
                # エラー時はデフォルト値で表示
                with prog_col1:
                    st.metric("📺 視聴回数", "0回", delta="未視聴")
                
                with prog_col2:
                    st.metric("⏱️ 視聴時間", "0分", delta="学習投資")
                
                with prog_col3:
                    st.metric("📚 理解度", "50%", delta="習得レベル")
                
                st.caption(f"⚠️ データ取得エラー: {str(e)}")
    
    st.caption("💡 健康な金魚は速く泳ぎ、弱った金魚はゆっくり泳ぎます。金魚をホバーすると詳細情報が表示されます。")
    
    # 自動リフレッシュ機能
    if st.checkbox("自動リフレッシュ（10秒毎）", value=False):
        import time
        time.sleep(10)
        st.rerun()
