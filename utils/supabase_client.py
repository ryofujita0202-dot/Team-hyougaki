"""Supabaseクライアントとユーザー認証機能"""
import re
import streamlit as st
from supabase import create_client, Client
from utils.config import settings
from typing import Optional, Dict, Any

def validate_email(email: str) -> bool:
    """メールアドレスの形式を検証"""
    # 基本的なメール形式チェック
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_japanese_domain(email: str) -> bool:
    """日本のドメインや企業ドメインの検証"""
    # よくある日本の企業ドメインやプロバイダー
    common_domains = [
        '.co.jp', '.or.jp', '.go.jp', '.ac.jp', '.ne.jp',
        '.com', '.net', '.org', '.info', '.biz'
    ]
    return any(email.endswith(domain) for domain in common_domains)

def get_user_data(user_obj) -> Dict[str, Any]:
    """Supabaseユーザーオブジェクトを統一的な辞書形式に変換"""
    if hasattr(user_obj, 'model_dump'):
        # Pydanticモデルの場合
        return user_obj.model_dump()
    elif hasattr(user_obj, '__dict__'):
        # 通常のオブジェクトの場合
        return dict(user_obj.__dict__)
    elif isinstance(user_obj, dict):
        # すでに辞書の場合
        return user_obj
    else:
        # その他の場合は空辞書を返す
        return {}

# Supabaseクライアントの初期化
@st.cache_resource
def get_supabase_client() -> Optional[Client]:
    """Supabaseクライアントを取得（シングルトン）"""
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        st.error("⚠️ SUPABASE設定が不完全です")
        st.info("""
        SUPABASEを使用するには、以下の手順で設定してください：
        
        1. https://supabase.com でアカウントを作成
        2. 新しいプロジェクトを作成
        3. Settings > API から URL と anon key を取得
        4. .env ファイルに設定を記入
        """)
        return None
    
    try:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    except Exception as e:
        error_msg = str(e)
        if "Invalid API key" in error_msg:
            st.error("🔑 SUPABASEのAPIキーが無効です")
            st.info("""
            解決方法：
            1. https://supabase.com でプロジェクトを確認
            2. Settings > API で新しいキーを生成
            3. .env ファイルを更新してアプリを再起動
            """)
        elif "JSON could not be generated" in error_msg:
            st.error("🔗 SUPABASEプロジェクトにアクセスできません")
            st.info("""
            考えられる原因：
            - プロジェクトが削除されている
            - APIキーの期限切れ
            - ネットワーク接続の問題
            """)
        else:
            st.error(f"Supabase接続エラー: {error_msg}")
        return None

def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """ユーザーログイン"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            st.error("Supabaseサービスが利用できません")
            return None
            
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        
        if response.user:
            # セッション情報をStreamlitセッションに保存（辞書形式で）
            user_dict = get_user_data(response.user)
            st.session_state.user = user_dict
            st.session_state.access_token = response.session.access_token if response.session else None
            
            # プロファイルが存在しない場合は作成
            try:
                supabase = get_supabase_client()
                profile_check = supabase.table("app_user").select("*").eq("auth_user_id", response.user.id).execute()
                
                if not profile_check.data:
                    # プロファイルが存在しないので作成
                    user_profile = {
                        "auth_user_id": response.user.id,
                        "display_name": email.split("@")[0],
                        "role": "child",
                        "created_at": "now()"
                    }
                    supabase.table("app_user").insert(user_profile).execute()
                    st.info("👤 プロファイルを作成しました")
                else:
                    # 既存のプロファイル情報をuser_dictにマージ
                    profile = profile_check.data[0]
                    user_dict.update({
                        'display_name': profile.get('display_name'),
                        'role': profile.get('role')
                    })
                    
            except Exception as profile_error:
                # プロファイル作成に失敗してもログイン自体は成功とする
                st.warning(f"プロファイル作成に失敗しましたが、ログインは成功しました: {str(profile_error)}")
            
            return {
                "success": True,
                "message": "ログイン成功",
                "user": user_dict
            }
        return {
            "success": False,
            "message": "ログインに失敗しました",
            "user": None
        }
    except Exception as e:
        error_msg = str(e).lower()
        
        if "invalid login credentials" in error_msg:
            st.error("❌ ログイン失敗: メールアドレスまたはパスワードが正しくありません")
            st.info("""
            🔍 **解決方法をお試しください：**
            
            **1. パスワード確認**
            - 大文字・小文字・数字・記号を正確に入力
            - CapsLockやNumLockの状態を確認
            
            **2. メール認証確認**
            - 登録時に送信されたメールを確認
            - 迷惑メールフォルダもチェック
            - 認証リンクをクリック済みか確認
            
            **3. アカウント再作成**
            - 別のメールアドレスで新規登録
            - またはパスワードリセット機能を使用（下記参照）
            """)
            
            # パスワードリセット機能の案内（フォーム外で処理するため）
            st.session_state.show_password_reset = True
            st.session_state.reset_email = email
                    
        elif "email not confirmed" in error_msg:
            st.error("❌ メール認証が完了していません")
            st.info("登録時に送信されたメールの確認リンクをクリックしてください")
            
            # メール認証再送信の案内（フォーム外で処理するため）
            st.session_state.show_resend_confirmation = True
            st.session_state.confirmation_email = email
        else:
            st.error(f"❌ ログインエラー: {str(e)}")
        return {
            "success": False,
            "message": str(e),
            "user": None
        }

def register_user(email: str, password: str, display_name: str = "") -> Optional[Dict[str, Any]]:
    """ユーザー登録"""
    # メール形式の事前検証
    if not validate_email(email):
        st.error("❌ メールアドレスの形式が正しくありません")
        st.info("例: user@example.com のような形式で入力してください")
        return None
    
    # 日本のドメイン形式の検証
    if not validate_japanese_domain(email):
        st.warning("⚠️ 入力されたドメインが一般的ではありません")
        st.info("一般的なドメイン例: .co.jp, .com, .net, .org など")
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            st.error("❌ Supabaseサービスが利用できません")
            st.info("SUPABASEの設定を確認してください")
            return None
        
        # デバッグ情報を表示
        st.info(f"登録試行中: {email}")
        
        response = supabase.auth.sign_up({"email": email, "password": password})
        
        if response.user:
            # メール認証状態をチェック
            user_confirmed = getattr(response.user, 'email_confirmed_at', None)
            
            if not user_confirmed:
                st.success("✅ アカウント作成成功")
                st.info("📧 登録確認のメールを送信しました。メールボックスを確認して、認証リンクをクリックしてください。")
                st.warning("⚠️ メール認証完了後にログインしてください")
                # メール認証未完了の場合はapp_userテーブル挿入をスキップ
                return {
                    "success": True,
                    "message": "メール認証が必要です",
                    "user": None,
                    "email_confirmation_required": True
                }
            
            # メール認証済みの場合のみapp_userテーブルに挿入
            try:
                user_profile = {
                    "auth_user_id": response.user.id,
                    "display_name": display_name or email.split("@")[0],
                    "role": "child",  # デフォルトは子ユーザー
                    "created_at": "now()"
                }
                
                # app_userテーブルに挿入
                supabase.table("app_user").insert(user_profile).execute()
                
                # セッション情報をStreamlitセッションに保存（辞書形式で）
                user_dict = get_user_data(response.user)
                st.session_state.user = user_dict
                st.session_state.access_token = response.session.access_token if response.session else None
                return {
                    "success": True,
                    "message": "登録とプロフィール作成が完了しました",
                    "user": user_dict
                }
                
            except Exception as profile_error:
                st.error(f"❌ プロファイル作成エラー: {str(profile_error)}")
                # 認証は成功したが、プロファイル作成に失敗
                st.info("アカウントは作成されましたが、プロファイル作成に失敗しました。ログイン後に再度お試しください。")
                return {
                    "success": False,
                    "message": f"プロファイル作成エラー: {str(profile_error)}",
                    "user": None
                }
        else:
            st.warning("⚠️ ユーザー登録に失敗しました")
            if hasattr(response, 'session') and response.session is None:
                st.info("メール確認が必要かもしれません。メールをチェックしてください。")
        return {
            "success": False,
            "message": "ユーザー登録に失敗しました",
            "user": None
        }
    except Exception as e:
        error_msg = str(e).lower()
        
        if "infinite recursion detected in policy" in error_msg:
            st.error("❌ データベースポリシーエラーが発生しました")
            st.info("""
            解決方法:
            1. SUPABASEダッシュボードの「SQL Editor」を開く
            2. 以下のSQLを実行してポリシーを修正:
            
            ```sql
            ALTER TABLE app_user DISABLE ROW LEVEL SECURITY;
            ```
            
            3. または、プロジェクトのfix_rls_policies.sqlファイルを実行
            4. アプリケーションを再起動
            """)
            with st.expander("技術的な詳細"):
                st.code(f"エラーコード: 42P17\nメッセージ: {str(e)}")
        elif "invalid email" in error_msg or "email address is invalid" in error_msg:
            st.error("❌ メールアドレスが無効です")
            st.info("""
            解決方法:
            1. メールアドレスの形式を確認してください (例: user@example.com)
            2. 特殊文字や全角文字が含まれていないか確認
            3. 別のメールアドレスを試してみてください
            """)
        elif "user already registered" in error_msg or "already exists" in error_msg:
            st.error("❌ このメールアドレスは既に登録済みです")
            st.info("ログインを試すか、別のメールアドレスを使用してください")
        elif "invalid api key" in error_msg:
            st.error("❌ SUPABASE APIキーが無効です")
            st.info("新しいSUPABASEプロジェクトを作成し、APIキーを更新してください")
        else:
            st.error(f"❌ 登録エラー: {str(e)}")
            st.info("詳細なエラー情報を確認し、SUPABASEの設定を見直してください")
        return {
            "success": False,
            "message": str(e),
            "user": None
        }

def logout_user():
    """ユーザーログアウト"""
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
        
        # セッション情報をクリア
        if 'user' in st.session_state:
            del st.session_state.user
        if 'access_token' in st.session_state:
            del st.session_state.access_token
        if 'user_profile' in st.session_state:
            del st.session_state.user_profile
            
    except Exception as e:
        st.error(f"ログアウトエラー: {str(e)}")

def get_current_user() -> Optional[Dict[str, Any]]:
    """現在のログインユーザーを取得"""
    return getattr(st.session_state, 'user', None)

def get_user_profile() -> Optional[Dict[str, Any]]:
    """現在のユーザープロファイルを取得"""
    if 'user_profile' in st.session_state:
        return st.session_state.user_profile
    
    user = get_current_user()
    if not user:
        return None
    
    try:
        supabase = get_supabase_client()
        
        # user オブジェクトの形式を確認してIDを取得
        user_id = None
        if isinstance(user, dict):
            user_id = user.get("id")
        elif hasattr(user, 'id'):
            user_id = user.id
        elif hasattr(user, '__dict__'):
            user_id = getattr(user, 'id', None)
        
        if not user_id:
            st.error("ユーザーIDを取得できませんでした")
            return None
        
        response = supabase.table("app_user").select("*").eq("auth_user_id", user_id).execute()
        
        if response.data:
            st.session_state.user_profile = response.data[0]
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"ユーザープロファイル取得エラー: {str(e)}")
        return None

def is_authenticated() -> bool:
    """認証状態をチェック"""
    return get_current_user() is not None

def require_auth():
    """認証が必要なページで使用するデコレータ的な関数"""
    if not is_authenticated():
        st.warning("この機能を使用するにはログインが必要です。")
        return False
    return True

def get_current_user_id() -> Optional[str]:
    """現在のユーザーIDを取得"""
    user = get_current_user()
    if not user:
        return None
    
    # user オブジェクトの形式を確認してIDを取得
    if isinstance(user, dict):
        return user.get("id")
    elif hasattr(user, 'id'):
        return user.id
    elif hasattr(user, '__dict__'):
        return getattr(user, 'id', None)
    
    return None