import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import plotly.express as px
import plotly.graph_objects as go

from utils.supabase_client import (
    get_current_user, require_auth, get_user_profile, get_supabase_client
)
from repositories.supabase_repo import fetch_view_logs, get_user_stats

def get_family_members() -> List[Dict[str, Any]]:
    """家族メンバーの一覧を取得（親の場合）"""
    user = get_current_user()
    if not user:
        return []
    
    try:
        supabase = get_supabase_client()
        profile = get_user_profile()
        
        if not profile or profile.get("role") != "parent":
            return []
        
        family_id = profile.get("family_id")
        if not family_id:
            return []
        
        # 同じfamily_idの子ユーザーを取得
        response = supabase.table("app_user")\
            .select("*")\
            .eq("family_id", family_id)\
            .execute()
        
        return response.data
    except Exception as e:
        st.error(f"家族メンバー取得エラー: {e}")
        return []

def render_family_dashboard():
    """家族全体のダッシュボード"""
    st.subheader("👨‍👩‍👧‍👦 家族学習ダッシュボード")
    
    family_members = get_family_members()
    
    if not family_members:
        st.info("家族メンバーが見つかりません。家族IDの設定を確認してください。")
        return
    
    # 各メンバーの統計取得
    all_stats = {}
    all_logs = {}
    
    for member in family_members:
        user_id = member["auth_user_id"]
        stats = get_user_stats(user_id)
        logs = fetch_view_logs(user_id, limit=100)
        
        all_stats[member["display_name"]] = stats
        all_logs[member["display_name"]] = logs
    
    # 全体統計
    st.subheader("📊 全体統計")
    
    total_videos = sum(stats["total_videos"] for stats in all_stats.values())
    total_time = sum(stats["total_watch_time"] for stats in all_stats.values())
    total_views = sum(stats["total_views"] for stats in all_stats.values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👨‍👩‍👧‍👦 家族全体の視聴動画数", total_videos)
    with col2:
        hours = total_time // 3600
        minutes = (total_time % 3600) // 60
        st.metric("⏱️ 家族全体の視聴時間", f"{hours}h {minutes}m")
    with col3:
        st.metric("🔄 家族全体の視聴回数", total_views)
    
    # メンバー別統計
    st.subheader("👤 メンバー別統計")
    
    member_data = []
    for name, stats in all_stats.items():
        member_data.append({
            "メンバー": name,
            "動画数": stats["total_videos"],
            "視聴時間(分)": stats["total_watch_time"] // 60,
            "視聴回数": stats["total_views"]
        })
    
    if member_data:
        df = pd.DataFrame(member_data)
        
        # 棒グラフ
        fig = px.bar(df, x="メンバー", y="動画数", title="メンバー別視聴動画数")
        st.plotly_chart(fig, use_container_width=True)
        
        # データテーブル
        st.dataframe(df, use_container_width=True)

def render_comprehension_analysis():
    """理解度分析"""
    st.subheader("🧠 理解度分析")
    
    family_members = get_family_members()
    if not family_members:
        st.info("分析するデータがありません")
        return
    
    comprehension_data = []
    
    for member in family_members:
        user_id = member["auth_user_id"]
        logs = fetch_view_logs(user_id, limit=100)
        
        for log in logs:
            comprehension_level = log.get("comprehension_level")
            if comprehension_level:
                comprehension_text = {
                    1: "①覚えた",
                    2: "②普通", 
                    3: "③覚えていない"
                }.get(comprehension_level, "未評価")
                
                comprehension_data.append({
                    "メンバー": member["display_name"],
                    "理解度": comprehension_text,
                    "日付": datetime.fromisoformat(log['watched_at'].replace('Z', '+00:00')).date()
                })
    
    if comprehension_data:
        df = pd.DataFrame(comprehension_data)
        
        # 理解度の分布
        fig = px.histogram(df, x="理解度", color="メンバー", title="理解度の分布")
        st.plotly_chart(fig, use_container_width=True)
        
        # 時系列の理解度
        if len(df) > 1:
            df_time = df.groupby(['日付', '理解度']).size().reset_index(name='件数')
            fig_time = px.line(df_time, x="日付", y="件数", color="理解度", title="理解度の推移")
            st.plotly_chart(fig_time, use_container_width=True)

def render_recent_activity():
    """最近の学習活動"""
    st.subheader("📅 最近の学習活動")
    
    family_members = get_family_members()
    if not family_members:
        return
    
    recent_logs = []
    
    for member in family_members:
        user_id = member["auth_user_id"]
        logs = fetch_view_logs(user_id, limit=20)
        
        for log in logs:
            comprehension_level = log.get("comprehension_level")
            comprehension_text = "❓ 未評価"
            if comprehension_level:
                comprehension_mapping = {
                    1: "🟢 ①覚えた",
                    2: "🟡 ②普通", 
                    3: "🔴 ③覚えていない"
                }
                comprehension_text = comprehension_mapping.get(comprehension_level, "❓ 未評価")
            
            recent_logs.append({
                "メンバー": member["display_name"],
                "動画ID": log["video_id"],
                "理解度": comprehension_text,
                "視聴日時": datetime.fromisoformat(log['watched_at'].replace('Z', '+00:00')),
                "メモ": log.get("note", "")[:50] + ("..." if len(log.get("note", "")) > 50 else "")
            })
    
    # 日時順でソート
    recent_logs.sort(key=lambda x: x["視聴日時"], reverse=True)
    
    # 最新10件を表示
    for log in recent_logs[:10]:
        with st.container():
            col1, col2, col3 = st.columns([2, 3, 2])
            
            with col1:
                st.write(f"**{log['メンバー']}**")
                st.caption(log["視聴日時"].strftime("%m/%d %H:%M"))
            
            with col2:
                youtube_url = f"https://www.youtube.com/watch?v={log['動画ID']}"
                st.markdown(f"🎬 [{log['動画ID']}]({youtube_url})")
                if log["メモ"]:
                    st.caption(f"📝 {log['メモ']}")
            
            with col3:
                st.write(log["理解度"])
            
            st.divider()

def render_goals_and_rewards():
    """目標設定と報酬システム"""
    st.subheader("🎯 目標設定と報酬")
    
    # これは将来の拡張機能として簡単な表示のみ
    st.info("🚧 目標設定機能は開発中です")
    
    # 簡単な進捗表示
    family_members = get_family_members()
    if family_members:
        st.write("**今週の学習目標達成状況**")
        
        for member in family_members:
            user_id = member["auth_user_id"]
            
            # 今週のログを取得
            week_ago = datetime.now() - timedelta(days=7)
            logs = fetch_view_logs(user_id, limit=100)
            
            # 今週の学習をフィルタ
            week_logs = [
                log for log in logs 
                if datetime.fromisoformat(log['watched_at'].replace('Z', '+00:00')) > week_ago
            ]
            
            # 進捗表示
            progress = min(len(week_logs) / 5.0, 1.0)  # 週5本を目標とする
            st.progress(progress, text=f"{member['display_name']}: {len(week_logs)}/5本")

def render_parent_view():
    """親ビューのメイン関数"""
    st.title("👨‍👩‍👧‍👦 親ビュー - 家族学習ダッシュボード")
    
    if not require_auth():
        return
    
    profile = get_user_profile()
    if not profile:
        st.error("ユーザープロファイルを取得できません")
        return
    
    if profile.get("role") != "parent":
        st.warning("親ユーザーとしてログインしてください")
        st.info("現在はログインでの機能をご利用ください")
        return
    
    # タブ構成
    tab1, tab2, tab3, tab4 = st.tabs(["📊 全体統計", "🧠 理解度分析", "📅 最近の活動", "🎯 目標・報酬"])
    
    with tab1:
        render_family_dashboard()
    
    with tab2:
        render_comprehension_analysis()
    
    with tab3:
        render_recent_activity()
    
    with tab4:
        render_goals_and_rewards()