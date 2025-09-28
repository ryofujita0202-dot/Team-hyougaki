import streamlit as st

def video_card(v, fish, views_count: int, on_view_click):
    col1, col2 = st.columns([1,2])
    with col1:
        if v.thumbnail_url: 
            try:
                st.image(v.thumbnail_url, use_container_width=True)
            except Exception as e:
                st.warning(f"サムネイル読み込みエラー: {e}")
        else:
            st.info("サムネイル画像なし")
    with col2:
        st.subheader(v.title)
        st.caption(v.url)
        st.text(f"視聴回数: {views_count}")
        if fish:
            st.text(f"金魚: health={fish.health}  weight={fish.weight_g}g  状態={fish.status}")
            if fish.next_due:
                try:
                    st.text(f"次回復習: {fish.next_due.strftime('%Y-%m-%d')}")
                except Exception:
                    pass
        if st.button("視聴した！", key=f"view_{v.id}"):
            on_view_click()
