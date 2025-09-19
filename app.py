import streamlit as st
from utils.config import settings

st.set_page_config(page_title="GyoLog", page_icon="🐟", layout="centered")
st.title("GyoLog（ギョログ）")
st.caption("学んだ動画に Wikipedia＋AI 要約を添えて、“学びの泳跡”をログ化。")

with st.sidebar:
    page = st.radio("ページ", ["ホーム", "子ビュー", "親ビュー"], index=0)
    st.write({"YouTubeAPI": bool(settings.YOUTUBE_API_KEY),
              "Gemini": bool(settings.GOOGLE_AI_STUDIO_API_KEY),
              "Supabase": bool(settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY)})

if page == "ホーム":
    st.markdown("- 左のメニューから画面を切り替えてください。")
elif page == "子ビュー":
    from views.child_view import render as render_child
    render_child()
elif page == "親ビュー":
    from views.parent_view import render as render_parent
    render_parent()


git commit -m "アプリの起動スクリプト（エントリーポイント）"
git push
