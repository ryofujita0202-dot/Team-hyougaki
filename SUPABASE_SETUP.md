# Supabase統合セットアップガイド

このガイドでは、Learning Fish TankアプリケーションにSupabaseを統合し、ユーザー認証と学習データ管理を実装する手順を説明します。

## 🎯 実装された機能

### ✅ ユーザー認証機能
- **ユーザー登録/ログイン**: メールアドレスとパスワードでの認証
- **ユーザープロファイル管理**: 表示名、役割（親/子）、家族ID
- **セッション管理**: Streamlitセッションでの認証状態維持

### ✅ 学習データ管理
- **YouTubeURL登録**: 動画IDの自動抽出
- **視聴記録**: 視聴時間、回数、メモの記録
- **理解度評価**: ①覚えた/②普通/③覚えていない の3段階評価
- **自動要約**: Wikipedia要約とGemini AI要約の生成

### ✅ データベース構造
- **app_user**: ユーザープロファイル（親子関係管理）
- **view_log**: 視聴ログ（理解度評価、メモ、要約含む）
- **video**: 動画メタデータキャッシュ
- **achievement**: 実績・バッジ（将来の拡張用）

### ✅ 親子機能
- **ログイン**: 学習登録、履歴確認、統計表示
- **親ビュー**: 家族全体のダッシュボード、理解度分析

## 🚀 セットアップ手順

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. Supabaseプロジェクトの作成

1. [Supabase](https://supabase.com)でアカウント作成
2. 新しいプロジェクトを作成
3. プロジェクト設定からURL、API Keyを取得

### 3. 環境変数の設定

`.env`ファイルを編集し、以下を設定：

```env
# Supabase設定
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# Google AI Studio API（要約機能用）
GOOGLE_AI_STUDIO_API_KEY=your_google_ai_studio_api_key_here
```

### 4. データベーススキーマの設定

Supabaseダッシュボードの「SQL Editor」で、`db/schema.sql`の内容を実行してテーブルとポリシーを作成します。

### 5. Row Level Security (RLS) の確認

以下のテーブルでRLSが有効になっていることを確認：
- `app_user`
- `view_log` 
- `achievement`

## 📁 追加されたファイル構造

```
take learning-fish-tank - Ver6/
├── utils/
│   ├── config.py           # 環境変数設定
│   └── supabase_client.py  # Supabase認証機能
├── repositories/
│   └── supabase_repo.py    # データベース操作
├── models/
│   └── schemas.py          # データモデル定義
├── views/
│   └── child_view.py       # 子ユーザーUI
├── services/               # （既存のYouTube/AI機能）
├── db/
│   └── schema.sql          # データベーススキーマ
└── .env                    # 環境変数（追加設定）
```

## 🔧 使用方法

### 基本的なフロー

1. **ユーザー登録/ログイン**
   - アプリ起動時に認証UI表示
   - メールアドレスとパスワードで登録/ログイン

2. **動画登録**
   - YouTubeのURLを入力
   - 理解度（①覚えた/②普通/③覚えていない）を選択
   - メモを記入（任意）

3. **学習履歴確認**
   - 過去の視聴ログを一覧表示
   - 検索・フィルタ機能

4. **統計表示**
   - 総動画数、視聴時間、視聴回数

### 既存機能との統合

- **魚タンク表示**: 既存の魚タンク機能はそのまま利用可能
- **YouTube機能**: 既存のYouTube API連携はそのまま利用可能
- **ローカルDB**: SQLiteとSupabaseの併用が可能

## 🛡️ セキュリティ

- **Row Level Security**: ユーザーは自分のデータのみアクセス可能
- **親子関係**: 親ユーザーは家族のデータを閲覧可能
- **API Key管理**: 環境変数での安全な管理

## 🚨 トラブルシューティング

### よくあるエラー

1. **認証エラー**
   - SUPABASE_URLとSUPABASE_ANON_KEYが正しく設定されているか確認
   - Supabaseプロジェクトが有効か確認

2. **データベースエラー**
   - スキーマが正しく作成されているか確認
   - RLSポリシーが設定されているか確認

3. **依存関係エラー**
   - `pip install -r requirements.txt`で依存関係を再インストール

### デバッグ方法

```python
# Supabase接続テスト
from utils.supabase_client import get_supabase_client
try:
    client = get_supabase_client()
    print("Supabase接続成功")
except Exception as e:
    print(f"Supabase接続エラー: {e}")
```

## 📈 今後の拡張予定

- 親ダッシュボード機能の完全実装
- 実績・バッジシステム
- データ分析・レポート機能
- モバイル対応の改善