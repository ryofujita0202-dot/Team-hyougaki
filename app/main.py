import os
from datetime import datetime, timezone
import streamlit as st
import base64
import sys
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# ====== 初期化 & テーマ/スタイル ======
load_dotenv()

# 設定チェック機能
def check_configuration():
    """設定ファイルをチェックして警告を表示"""
    warnings = []
    
    # YouTube API キーのチェック
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")
    if not youtube_api_key or youtube_api_key == "YOUR_YOUTUBE_DATA_API_KEY" or "TEAM-SHARED" in youtube_api_key:
        warnings.append("🔑 YouTube API キーが正しく設定されていません。動画のメタデータ取得ができません。")
        warnings.append("💡 Google Cloud ConsoleでYouTube Data API v3のAPIキーを取得してください。")
    
    # Supabase設定のチェック
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    if not supabase_url or supabase_url == "https://your-project-id.supabase.co":
        warnings.append("🔗 Supabase URL が設定されていません。クラウド機能が利用できません。")
    if not supabase_key or supabase_key == "your_supabase_anon_key_here":
        warnings.append("🔑 Supabase API キーが設定されていません。ログイン機能が利用できません。")
    
    return warnings

# 設定警告の表示
config_warnings = check_configuration()
if config_warnings:
    with st.sidebar:
        st.warning("⚠️ 設定の注意点")
        for warning in config_warnings:
            st.caption(warning)
        st.caption("完全な機能を使用するには .env ファイルを設定してください。")

# ロゴを先に検出して、ページアイコン（タブのアイコン）にも流用する
POSSIBLE_LOGO_PATHS = [
    os.path.join(os.path.dirname(__file__), "static", "logo.png"),
    os.path.join(os.path.dirname(__file__), "logo.png"),
    os.path.join(os.getcwd(), "logo.png"),
]
logo_path = None
for p in POSSIBLE_LOGO_PATHS:
    if os.path.exists(p):
        logo_path = p
        break

page_icon = logo_path if logo_path else "🐟"
st.set_page_config(page_title="Gyolog", page_icon=page_icon, layout="wide")

# If page is provided via query params (from nav links), use it to set session state
# Prefer the stable API and avoid calling the experimental API entirely to prevent
# deprecation messages being shown in the app UI.
if hasattr(st, 'get_query_params'):
    try:
        qparams = st.get_query_params()
    except Exception:
        qparams = {}
else:
    # Older Streamlit without stable API: don't call experimental API to avoid banners.
    qparams = {}

if 'page' in qparams:
    p = qparams.get('page')[0]
    if p in ('reg', 'list', 'tank', 'supabase'):
        st.session_state['page'] = p

# 必須パッケージのチェック: sqlmodel が無ければ UI 上で親切にエラーを表示して停止
try:
    from sqlmodel import select
    from sqlalchemy.orm import selectinload
except Exception:
    st.error("Missing required package 'sqlmodel'. Please install dependencies (see requirements.txt) and restart the app.")
    st.caption("PowerShell 例: python -m venv .venv ; .venv\\Scripts\\Activate.ps1 ; pip install -r requirements.txt")
    # ここで処理を止める
    st.stop()


from PIL import Image, ImageDraw

# モデルを先にインポートしてからデータベース初期化
from app.lib.models import Video, View, Fish
from app.lib.db import init_db, get_session
from app.lib.youtube import fetch_meta
from app.lib.summary import simple_summary
from app.lib.forgetting import update_fish_state

# データベース初期化を実行（エラーハンドリング追加）
try:
    init_db()
except Exception as e:
    st.error(f"データベース初期化エラー: {str(e)}")
    st.info("アプリケーションの再起動を試してください。")

# ヘッダ用: 画像を base64 埋め込みにして透明背景で表示するユーティリティ
def _img_to_data_uri(path: str) -> str:
    """Return data URI for a PNG/JPEG image at path."""
    with open(path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("ascii")
    # assume PNG, streamlit will render standard data URI
    return f"data:image/png;base64,{b64}"


def _ensure_transparent_logo(path: str) -> str:
    """
    If the PNG has premultiplied white fringe, attempt to fix by un-premultiplying RGB by alpha
    and write a processed file as logo_processed.png next to the original. Returns the path to use.
    """
    try:
        from PIL import Image
        import numpy as np
    except Exception:
        return path

    img = Image.open(path).convert('RGBA')
    arr = np.array(img)
    alpha = arr[:, :, 3].astype('float32')
    # find pixels with partial transparency
    mask = (alpha > 0) & (alpha < 255)
    if not mask.any():
        return path

    rgb = arr[:, :, :3].astype('float32')
    # detect white-fringe: where RGB are very close to 255 while alpha < 255
    whiteish = (rgb >= 250).all(axis=2)
    fringe = whiteish & mask
    frac = fringe.mean()
    # if small fraction of pixels are white-fringe, attempt unpremultiply
    if frac < 0.001:
        # likely not a premultiplied-white issue
        return path

    # un-premultiply RGB by alpha, then clip to [0, 255]
    alpha_factor = alpha / 255.0
    alpha_factor[alpha_factor == 0] = 1  # avoid division by zero
    rgb_un = rgb / alpha_factor[:, :, None]
    rgb_un = np.clip(rgb_un, 0, 255).astype('uint8')
    arr[:, :, :3] = rgb_un

    processed_path = path.replace('.png', '_processed.png')
    Image.fromarray(arr, 'RGBA').save(processed_path)
    return processed_path


# 簡単なスタイル
st.markdown("""
<style>
.main {
    background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
    min-height: 100vh;
}
h1, h2 { 
    color: #111; 
    text-shadow: none; 
}
</style>
""", unsafe_allow_html=True)

# ヘッダーロゴ表示
if logo_path:
    processed_logo = _ensure_transparent_logo(logo_path)
    logo_uri = _img_to_data_uri(processed_logo)
    header_html = f"""
    <div style="text-align: center; margin: 0 0 2rem 0; padding: 1rem;">
        <img src="{logo_uri}" alt="Gyolog Logo" style="max-height: 180px; max-width: 100%; height: auto; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));">
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

# ナビゲーション
st.markdown('<div class="nav-wrapper">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("📝 動画登録", use_container_width=True):
        st.session_state['page'] = 'reg'
        st.rerun()
with col2:
    if st.button("📋 動画一覧", use_container_width=True):
        st.session_state['page'] = 'list'
        st.rerun()
with col3:
    if st.button("🐠 水槽", use_container_width=True):
        st.session_state['page'] = 'tank'
        st.rerun()
with col4:
    if st.button("🔑 ログイン", use_container_width=True):
        st.session_state['page'] = 'supabase'
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ページセッション管理: デフォルトは登録ページ
if 'page' not in st.session_state:
    st.session_state['page'] = 'reg'

# ====== ① 動画登録ページ ======
if st.session_state.get('page') == 'reg':
    st.subheader("YouTube動画を登録")
    
    with st.form("video_registration_form"):
        url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...", help="YouTubeの動画URLを入力してください")
        
        # 理解度評価機能を追加
        comprehension = st.selectbox(
            "理解度",
            options=[1, 2, 3],
            format_func=lambda x: {1: "①覚えた", 2: "②普通", 3: "③覚えていない"}[x],
            index=1,
            help="動画を視聴した後の理解度を評価してください"
        )
        
        # 視聴時間（分）
        watch_minutes = st.number_input("視聴時間（分）", min_value=0, value=0, help="動画を視聴した時間を記録してください")
        
        # メモ（任意）
        note = st.text_area("メモ（任意）", placeholder="この動画について覚えておきたいこと...")
        
        submit = st.form_submit_button("登録")
    
    if submit:
        if url.strip():
            with st.spinner("動画情報を取得中..."):
                try:
                    meta = fetch_meta(url)
                    if not meta or not meta.get("title"):
                        # APIキーの問題かネットワークの問題かを判断
                        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
                        if not youtube_api_key or "TEAM-SHARED" in youtube_api_key:
                            st.error("登録エラー: YouTube APIキーが正しく設定されていません")
                            st.info("💡 解決方法: .envファイルで有効なYouTube Data API v3キーを設定してください")
                        else:
                            st.error("登録エラー: 動画情報の取得に失敗しました")
                            st.info("💡 YouTubeのURLが正しいか確認してください")
                        meta = None
                except Exception as e:
                    error_msg = str(e)
                    if "Invalid API key" in error_msg:
                        st.error("登録エラー: YouTube APIキーが無効です")
                        st.info("💡 解決方法: Google Cloud ConsoleでYouTube Data API v3の有効なAPIキーを取得し、.envファイルに設定してください")
                    else:
                        st.error(f"登録エラー: ネットワーク接続を確認してください ({error_msg})")
                    meta = None
                    
            if meta and meta.get("title"):
                # DB登録処理
                with get_session() as session:
                    v = Video(
                        url=url,
                        video_id=meta.get("video_id", ""),
                        title=meta["title"],
                        description=meta.get("description", ""),
                        thumbnail_url=meta.get("thumbnail_url", ""),
                        # 評価情報を追加で保存（メタデータとして）
                        created_at=datetime.now()
                    )
                    session.add(v)
                    session.commit()
                    
                    # 登録と同時に Fish も作成する
                    import random
                    # 金魚の色をランダムに選択
                    fish_colors = [
                        "#FF6B6B",  # 赤
                        "#4ECDC4",  # シアン
                        "#45B7D1",  # 青
                        "#96CEB4",  # 緑
                        "#FFEAA7",  # 黄色
                        "#DDA0DD",  # プラム
                        "#FFA07A",  # サーモン
                        "#98D8C8",  # ミントグリーン
                        "#F7DC6F",  # レモン
                        "#BB8FCE"   # 薄紫
                    ]
                    fish_color = random.choice(fish_colors)
                    
                    fish = Fish(
                        video_id=v.id,
                        health=50,  # 初期健康度を50%に変更
                        weight_g=100,
                        fish_color=fish_color
                    )
                    session.add(fish)
                    
                    # 登録時に視聴記録も作成（理解度、視聴時間、メモを含む）
                    if comprehension or watch_minutes > 0 or note.strip():
                        view_record = View(
                            video_id=v.id,
                            duration_sec=int(watch_minutes * 60) if watch_minutes > 0 else None,
                            comprehension=comprehension,
                            note=note.strip() if note.strip() else None,
                            viewed_at=datetime.now()
                        )
                        session.add(view_record)
                    
                    session.commit()
                
                # Supabaseにも学習ログとして保存（ログインしている場合）
                try:
                    if st.session_state.get('user_id'):
                        # YouTube URLから動画IDを抽出
                        import re
                        video_id_match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]+)', url)
                        if video_id_match:
                            video_id = video_id_match.group(1)
                            
                            from repositories.supabase_repo import save_view_log
                            from models.schemas import ViewLog, ComprehensionLevel
                            
                            view_log = ViewLog(
                                user_id=st.session_state['user_id'],
                                video_id=video_id,
                                watched_at=datetime.now(),
                                watch_seconds=int(watch_minutes * 60),
                                comprehension_level=ComprehensionLevel(comprehension),
                                note=note,
                                thumbnail_url=meta.get("thumbnail_url", f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
                            )
                            
                            save_view_log(view_log)
                except Exception as log_error:
                    # Supabaseログ保存エラーは警告のみ（ローカルDB保存は成功しているため）
                    st.warning(f"学習ログ保存に失敗しました: {log_error}")
                
                # 評価情報を表示
                comprehension_text = {1: "①覚えた", 2: "②普通", 3: "③覚えていない"}[comprehension]
                success_msg = f"動画「{meta['title']}」を登録しました！\n"
                success_msg += f"理解度: {comprehension_text}"
                if watch_minutes > 0:
                    success_msg += f" | 視聴時間: {watch_minutes}分"
                if note.strip():
                    success_msg += f" | メモ: {note[:50]}{'...' if len(note) > 50 else ''}"
                
                st.success(success_msg)
            else:
                st.error("動画の情報を取得できませんでした。URLを確認してください。")
        else:
            st.warning("URLを入力してください。")

# ====== ② 動画一覧・管理ページ ======
elif st.session_state.get('page') == 'list':
    st.subheader("登録済み動画一覧")
    
    try:
        with get_session() as session:
            videos = session.exec(select(Video)).all()
            # 新しいものから表示するために逆順にする（IDが大きいものから）
            videos = sorted(videos, key=lambda x: x.id or 0, reverse=True)
    except Exception as e:
        st.error(f"データベースエラー: {e}")
        videos = []
    
    if not videos:
        st.info("まだ動画が登録されていません。")
    else:
        for v in videos:
            with st.expander(f"📹 {v.title}", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**URL**: {v.url}")
                    if v.description:
                        summary, keywords = simple_summary(v.title, v.description)
                        st.write(f"**概要**: {summary}")
                    
                    # サムネイル表示（もしあれば）
                    if v.thumbnail_url:
                        try:
                            st.image(v.thumbnail_url, width=200, caption="動画サムネイル")
                        except Exception as e:
                            st.warning(f"サムネイル画像を読み込めませんでした: {e}")
                            st.text(f"サムネイルURL: {v.thumbnail_url}")
                    
                    # (金魚の色表示/変更は削除されました)
                
                with col2:
                    # 集計情報: 合計視聴時間, 理解度の平均, 全メモ
                    with get_session() as s_stats:
                        views = s_stats.exec(select(View).where(View.video_id==v.id)).all()
                        total_seconds = sum((vv.duration_sec or 0) for vv in views)
                        comp_vals = [getattr(vv, 'comprehension', None) for vv in views if getattr(vv, 'comprehension', None) is not None]
                        avg_comprehension = (sum(comp_vals) / len(comp_vals)) if comp_vals else None
                        # 全てのメモを時系列順（新しい順）で取得
                        all_notes = [(vv.note, vv.viewed_at) for vv in sorted(views, key=lambda x: x.viewed_at, reverse=True) if vv.note and vv.note.strip()]

                    if total_seconds > 0:
                        st.caption(f"合計視聴時間: {total_seconds//60}分 {total_seconds%60}秒")
                    else:
                        st.caption("合計視聴時間: 0分")

                    if avg_comprehension:
                        comp_label = {1: '①覚えた', 2: '②普通', 3: '③覚えていない'}
                        st.caption(f"理解度（平均）: {comp_label.get(round(avg_comprehension), round(avg_comprehension))}")
                    else:
                        st.caption("理解度: 記録なし")

                    # 全てのメモを表示
                    if all_notes:
                        if len(all_notes) == 1:
                            # メモが1つだけの場合は直接表示
                            note_text, _ = all_notes[0]
                            st.caption(f"メモ: {note_text[:120]}{'...' if len(note_text) > 120 else ''}")
                        else:
                            # 複数のメモがある場合はexpanderで表示
                            with st.expander(f"全メモを表示 ({len(all_notes)}個)", expanded=False):
                                for i, (note_text, note_date) in enumerate(all_notes, 1):
                                    st.markdown(f"**{i}.** {note_date.strftime('%m/%d %H:%M')}")
                                    st.markdown(f"　{note_text}")
                                    if i < len(all_notes):
                                        st.markdown("---")
                    else:
                        st.caption("メモ: なし")

                    # 視聴入力フォーム（expander 内フォーム）
                    with st.expander("視聴記録", expanded=False):
                        with st.form(key=f"view_form_{v.id}"):
                            comp = st.selectbox("理解度", options=[1,2,3], format_func=lambda x: {1:'①覚えた',2:'②普通',3:'③覚えていない'}[x], index=1)
                            minutes = st.number_input("視聴時間（分）", min_value=0, value=0, step=1)
                            submit_view = st.form_submit_button("視聴を記録")

                        if submit_view:
                            with get_session() as s2:
                                duration_sec = int(minutes * 60)
                                new_view = View(video_id=v.id, duration_sec=duration_sec, note=None, comprehension=comp)
                                s2.add(new_view)
                                # 対応する Fish を取得して更新（存在しない場合は警告）
                                f2 = s2.exec(select(Fish).where(Fish.video_id==v.id)).first()
                                try:
                                    views_after = s2.exec(select(View).where(View.video_id==v.id)).all()
                                    view_count = len(views_after)
                                except Exception:
                                    view_count = 0
                                if f2 is None:
                                    st.warning("関連する Fish レコードが見つかりません。Fish は動画登録時に自動作成されます。")
                                else:
                                    update_fish_state(f2, datetime.utcnow(), reviewed_today=True, view_count=view_count)
                                    s2.add(f2)
                                s2.commit()
                            st.success("視聴を記録しました。")
                            # Use stable API if available; some Streamlit versions removed experimental_rerun
                            try:
                                st.rerun()
                            except Exception:
                                # Last-resort fallback: no-op (UI will update on next interaction)
                                pass

                with col3:
                    # 削除ボタン（2段階確認）
                    del_key = f"del_{v.id}"
                    confirm_key = f"del_confirm_{v.id}"
                    # 第1段階: 削除ボタンを押すと session_state に確認フラグを立てる
                    if st.button("削除", key=del_key):
                        st.session_state[confirm_key] = True

                    # 確認フラグが立っている場合は注意文と確定ボタンを表示
                    if st.session_state.get(confirm_key):
                        st.warning("本当にこの動画と関連データを削除しますか？取り消せません。")
                        if st.button("本当に削除する", key=confirm_key+"_ok"):
                            # トランザクションで関連レコードを削除
                            with get_session() as s3:
                                # Views を全て削除
                                views_del = s3.exec(select(View).where(View.video_id==v.id)).all()
                                for vv in views_del:
                                    s3.delete(vv)
                                # Fish を削除（もし存在すれば）
                                fish_del = s3.exec(select(Fish).where(Fish.video_id==v.id)).first()
                                if fish_del:
                                    s3.delete(fish_del)
                                # Video 本体を削除
                                v_del = s3.exec(select(Video).where(Video.id==v.id)).first()
                                if v_del:
                                    s3.delete(v_del)
                                s3.commit()
                            # 確認フラグを消してからリロード
                            st.session_state.pop(confirm_key, None)
                            st.success("削除しました。")
                            st.rerun()

        st.divider()

# ====== ③ 水槽（アニメーション金魚） ======
if st.session_state.get('page') == 'tank':
    from app.lib.animated_tank import render_animated_tank
    render_animated_tank()
    
    # 動的魚生成のテスト機能（ログインユーザー向け）
    if st.session_state.get('user_id'):
        st.markdown("---")
        st.subheader("🎣 動的魚生成テスト")
        
        # 金のこってぃくんテスト機能
        with st.expander("🏆 金のこってぃくんテスト"):
            st.info("魚の健康度を95%以上にして金のこってぃくんを表示できます")
            
            with get_session() as session:
                all_fish = session.exec(select(Fish)).all()
                if all_fish:
                    fish_options = []
                    for fish in all_fish:
                        video = session.exec(select(Video).where(Video.id == fish.video_id)).first()
                        video_title = video.title if video else f"動画ID {fish.video_id}"
                        fish_options.append((fish, f"{video_title} (現在の健康度: {fish.health}%)"))
                    
                    if fish_options:
                        selected_fish, selected_label = st.selectbox(
                            "健康度を変更する魚を選択:",
                            fish_options,
                            format_func=lambda x: x[1]
                        )
                        
                        new_health = st.slider("新しい健康度", 0, 100, selected_fish.health)
                        
                        if st.button("健康度を更新"):
                            selected_fish.health = new_health
                            session.add(selected_fish)
                            session.commit()
                            st.success(f"健康度を{new_health}%に更新しました！")
                            if new_health >= 95:
                                st.success("🏆 この魚は金のこってぃくんになります！水槽ページで確認してください。")
                            st.rerun()
                else:
                    st.info("まず動画を登録してください")
        
        with st.expander("動的魚生成機能をテスト"):
            from app.lib.dynamic_fish_generator import DynamicFishGenerator
            
            test_video_title = st.text_input("テスト用動画タイトル", "Python プログラミング 入門")
            test_video_description = st.text_input("テスト用動画説明", "プログラミングの基本を学ぶ")
            
            if st.button("魚を生成"):
                with st.spinner("魚を生成中..."):
                    generator = DynamicFishGenerator()
                    
                    # こってぃの高度な魚生成を使用
                    fish_base64 = generator.generate_fish_with_advanced_features(
                        video_title=test_video_title,
                        user_id=st.session_state['user_id'],
                        video_id="test_video_123",
                        youtube_views=50000,  # テスト用データ
                        published_at=datetime.now(timezone.utc),
                        user_comprehension=2.5,
                        user_view_count=3
                    )
                    
                    if fish_base64:
                        # ジャンル判定
                        genre = generator.detect_genre_from_title(test_video_title)
                        rank, size = generator.calculate_fish_rank_from_views_and_learning(
                            50000, datetime.now(timezone.utc), 2.5, 3
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("生成された魚")
                            st.image(
                                f"data:image/png;base64,{fish_base64}", 
                                caption=f"{rank}級の{genre}魚 (サイズ: {size[0]}x{size[1]})"
                            )
                        
                        with col2:
                            st.subheader("魚の詳細")
                            st.write(f"**ジャンル**: {genre}")
                            st.write(f"**ランク**: {rank}級")
                            st.write(f"**サイズ**: {size[0]}×{size[1]}px")
                            
                            st.subheader("テスト用データ")
                            st.write(f"**YouTube視聴回数**: 50,000回")
                            st.write(f"**ユーザー視聴回数**: 3回")
                            st.write(f"**理解度**: 2.5/3.0")
                            
                            colors = generator.generate_fish_colors_by_genre(genre)
                            st.subheader("カラーテーマ")
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.color_picker("メイン", colors['primary'], disabled=True)
                            with col_b:
                                st.color_picker("サブ", colors['secondary'], disabled=True)
                            with col_c:
                                st.color_picker("アクセント", colors['accent'], disabled=True)
                    else:
                        st.error("魚生成に失敗しました")
    else:
        st.info("💡 動的魚生成機能を使用するには、ログインしてください（🔑 ログインページ）")

# ====== ④ ログイン機能 ======
elif st.session_state.get('page') == 'supabase':
    st.subheader("🔑 ログイン・新規登録")
    
    # シンプルなログイン状態表示
    try:
        from utils.supabase_client import get_current_user, login_user, logout_user, register_user
        
        user = get_current_user()
        
        if user:
            st.success(f"ログイン中: {user.get('email', 'ユーザー')}")
            if st.button("ログアウト"):
                logout_user()
                st.rerun()
            
            st.info("ログイン中は動画登録時に学習ログが自動保存されます。")
        else:
            st.info("ログインすると学習履歴を記録できます。")
            
            # タブでログインと新規登録を切り替え
            login_tab, register_tab = st.tabs(["🔑 ログイン", "👤 新規登録"])
            
            with login_tab:
                with st.form("login_form"):
                    st.markdown("### ログイン")
                    email = st.text_input("メールアドレス", key="login_email")
                    password = st.text_input("パスワード", type="password", key="login_password")
                    login_submit = st.form_submit_button("ログイン")
                    
                    if login_submit and email and password:
                        result = login_user(email, password)
                        if result and result.get("success"):
                            st.session_state['user_id'] = result.get('user_id')
                            st.success("ログインしました！")
                            st.rerun()
                        else:
                            st.error("ログインに失敗しました。メールアドレスとパスワードを確認してください。")
            
            with register_tab:
                with st.form("register_form"):
                    st.markdown("### 新規登録")
                    
                    reg_email = st.text_input("メールアドレス", key="register_email", 
                                           help="例: user@example.com")
                    reg_password = st.text_input("パスワード", type="password", key="register_password",
                                              help="6文字以上の英数字")
                    reg_password_confirm = st.text_input("パスワード（確認）", type="password", key="register_password_confirm")
                    display_name = st.text_input("表示名（オプション）", key="register_display_name",
                                               help="空欄の場合はメールアドレスの@前の部分が使用されます")
                    
                    register_submit = st.form_submit_button("新規登録")
                    
                    if register_submit:
                        # バリデーション
                        if not reg_email or not reg_password:
                            st.error("メールアドレスとパスワードは必須です。")
                        elif len(reg_password) < 6:
                            st.error("パスワードは6文字以上で設定してください。")
                        elif reg_password != reg_password_confirm:
                            st.error("パスワードが一致しません。")
                        else:
                            # 新規登録実行
                            with st.spinner("アカウント作成中..."):
                                result = register_user(reg_email, reg_password, display_name)
                                if result and result.get("success"):
                                    st.success("✅ アカウントが作成されました！")
                                    st.info("� ログインタブからログインしてください。")
                                else:
                                    st.error("アカウント作成に失敗しました。しばらく待ってから再試行してください。")
                    
                    st.caption("⚠️ パスワードは安全に保管してください。")
            
    except ImportError as e:
        st.error(f"ログイン機能の読み込みに失敗しました: {e}")
        st.info("Supabase関連の依存関係をインストールしてください: pip install supabase")

# その他の機能やページがここに続く場合は追加してください