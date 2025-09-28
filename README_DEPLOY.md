# Gyolog - Learning Fish Tank

学習動画の管理と記憶定着を可視化するStreamlitアプリケーションです。

## 特徴

- 🐠 学習動画を金魚に変換して水槽で可視化
- 📊 忘却曲線に基づく記憶強度の管理
- 🎯 視聴履歴とレビューサイクルの最適化
- 🔄 Supabase連携によるクラウド同期

## デプロイ方法

### 1. Streamlit Cloud デプロイ

1. GitHubにリポジトリをpush
2. [Streamlit Cloud](https://streamlit.io/cloud) にアクセス
3. 「New app」をクリック
4. リポジトリとブランチを選択
5. Main file path: `app/main.py`
6. Advanced settings で環境変数を設定：
   - `YOUTUBE_API_KEY`: YouTube Data API v3 キー
   - `SUPABASE_URL`: Supabaseプロジェクト URL
   - `SUPABASE_ANON_KEY`: Supabase匿名キー

### 2. ローカル実行

```bash
# 仮想環境作成・有効化
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .envファイルを編集して実際のAPIキーを設定

# アプリ起動
streamlit run app/main.py
```

## 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `YOUTUBE_API_KEY` | YouTube Data API v3 キー | 推奨 |
| `SUPABASE_URL` | Supabase プロジェクト URL | オプション |
| `SUPABASE_ANON_KEY` | Supabase 匿名キー | オプション |

## 技術スタック

- **Frontend**: Streamlit
- **Database**: SQLite (ローカル) / Supabase (クラウド)
- **APIs**: YouTube Data API v3, Google Generative AI
- **Image Processing**: Pillow
- **Data Modeling**: SQLModel + Pydantic