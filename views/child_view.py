import streamlit as st
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import re
from typing import Optional

from utils.supabase_client import (
    login_user, register_user, logout_user, 
    get_current_user, require_auth, get_user_profile
)
from repositories.supabase_repo import (
    save_view_log, fetch_view_logs, get_user_stats, 
    update_view_count, search_view_logs
)
from models.schemas import ViewLog, ComprehensionLevel, VideoMeta, SummaryJson

def extract_video_id(url: str) -> Optional[str]:
    """YouTubeのURLから動画IDを抽出"""
    # 様々なYouTubeのURL形式に対応
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]+)',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def render_auth_section():
    """認証セクションの表示"""
    user = get_current_user()
    
    if user:
        profile = get_user_profile()
        display_name = profile.get("display_name", "ユーザー") if profile else "ユーザー"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"ようこそ、{display_name}さん！")
        with col2:
            if st.button("ログアウト"):
                logout_user()
                st.rerun()
    else:
        tab1, tab2 = st.tabs(["ログイン", "新規登録"])
        
        with tab1:
            st.subheader("ログイン")
            with st.form("login_form"):
                email = st.text_input("メールアドレス")
                password = st.text_input("パスワード", type="password")
                submit = st.form_submit_button("ログイン")
                
                if submit and email and password:
                    user = login_user(email, password)
                    if user:
                        st.success("ログインしました！")
                        st.rerun()
        
        with tab2:
            st.subheader("新規登録")
            with st.form("register_form"):
                email = st.text_input("メールアドレス", key="reg_email")
                password = st.text_input("パスワード", type="password", key="reg_password")
                display_name = st.text_input("表示名（任意）", key="reg_display_name")
                submit = st.form_submit_button("登録")
                
                if submit and email and password:
                    user = register_user(email, password, display_name)
                    if user:
                        st.success("登録が完了しました！")
                        st.rerun()

def render_video_registration():
    """動画登録セクション"""
    if not require_auth():
        return
    
    st.subheader("📹 動画の登録")
    
    with st.form("video_form"):
        url = st.text_input("YouTubeのURL", placeholder="https://www.youtube.com/watch?v=...")
        note = st.text_area("メモ（任意）", placeholder="この動画について...")
        
        # 理解度評価
        comprehension = st.selectbox(
            "理解度",
            options=[1, 2, 3],
            format_func=lambda x: {1: "①覚えた", 2: "②普通", 3: "③覚えていない"}[x],
            index=1
        )
        
        # 視聴時間（秒）
        watch_minutes = st.number_input("視聴時間（分）", min_value=0, value=0)
        
        submit = st.form_submit_button("登録")
        
        if submit and url:
            video_id = extract_video_id(url)
            if not video_id:
                st.error("有効なYouTubeのURLを入力してください")
                return
            
            current_user = get_current_user()
            if not current_user:
                st.error("ログインが必要です")
                return
            user_id = current_user["id"]
            
            # ViewLogオブジェクトを作成
            view_log = ViewLog(
                user_id=user_id,
                video_id=video_id,
                watched_at=datetime.now(),
                watch_seconds=int(watch_minutes * 60),
                comprehension_level=ComprehensionLevel(comprehension),
                note=note,
                thumbnail_url=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            )
            
            # データベースに保存
            if save_view_log(view_log):
                st.success("動画が登録されました！")
                st.rerun()
            else:
                st.error("登録に失敗しました")

def render_view_logs():
    """視聴ログ表示セクション"""
    if not require_auth():
        return
    
    st.subheader("📚 学習履歴")
    
    current_user = get_current_user()
    if not current_user:
        st.error("ログインが必要です")
        return
    user_id = current_user["id"]
    
    # 検索・フィルタ機能
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input("検索", placeholder="メモや要約から検索...")
    with col2:
        rating_filter = st.selectbox(
            "理解度でフィルタ",
            options=[None, 1, 2, 3],
            format_func=lambda x: "すべて" if x is None else {1: "①覚えた", 2: "②普通", 3: "③覚えていない"}[x]
        )
    
    # データを取得
    if search_query or rating_filter is not None:
        logs = search_view_logs(user_id, search_query, rating_filter)
    else:
        logs = fetch_view_logs(user_id)
    
    if not logs:
        st.info("まだ学習履歴がありません。動画を登録してみましょう！")
        return
    
    # ログを表示
    for log in logs:
        with st.expander(f"🎥 {log.get('video_id', 'Unknown')} - {log.get('comprehension_level', 'N/A')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if log.get('thumbnail_url'):
                    st.image(log['thumbnail_url'], width=200)
                
                if log.get('note'):
                    st.write("**メモ:**", log['note'])
                
                if log.get('wiki_summary'):
                    st.write("**要約:**", log['wiki_summary'])
            
            with col2:
                st.write("**視聴日時:**", log.get('watched_at', 'N/A'))
                if log.get('watch_seconds'):
                    minutes = log['watch_seconds'] // 60
                    st.write(f"**視聴時間:** {minutes}分")
                
                comprehension_text = "未評価"
                if log.get('comprehension_level'):
                    mapping = {1: "①覚えた", 2: "②普通", 3: "③覚えていない"}
                    comprehension_text = mapping.get(log['comprehension_level'], "未評価")
                st.write("**理解度:**", comprehension_text)
                
                st.write("**視聴回数:**", log.get('view_count_accum', 1))

def render_stats():
    """統計情報表示セクション"""
    if not require_auth():
        return
    
    st.subheader("📊 学習統計")
    
    current_user = get_current_user()
    if not current_user:
        st.error("ログインが必要です")
        return
    user_id = current_user["id"]
    stats = get_user_stats(user_id)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("総動画数", stats["total_videos"])
    
    with col2:
        total_minutes = stats["total_watch_time"] // 60
        st.metric("総視聴時間", f"{total_minutes}分")
    
    with col3:
        st.metric("総視聴回数", stats["total_views"])

def render_child_view():
    """子ユーザー向けのメインビュー"""
    st.title("🐟 Gyolog - 学習記録")
    
    # 認証セクション
    render_auth_section()
    
    # 認証されている場合のみ、以下のセクションを表示
    if get_current_user():
        st.divider()
        
        # タブで機能を分割
        tab1, tab2, tab3 = st.tabs(["動画登録", "学習履歴", "統計"])
        
        with tab1:
            render_video_registration()
        
        with tab2:
            render_view_logs()
        
        with tab3:
            render_stats()