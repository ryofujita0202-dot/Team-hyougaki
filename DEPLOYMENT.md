# Deployment Configuration

## Streamlit Cloud デプロイ設定

### 必要な設定
- **Main file path**: `app/main.py`
- **Python version**: 3.11.0
- **Port**: 8501 (自動)

### 環境変数 (Secrets)
```toml
# .streamlit/secrets.toml または Streamlit Cloud Advanced Settings
YOUTUBE_API_KEY = "your_youtube_api_key_here"
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your_supabase_anon_key_here"
```

### ファイル構成
```
├── app/main.py                 # エントリーポイント
├── requirements.txt            # Python依存関係
├── runtime.txt                # Python バージョン指定
├── Procfile                   # Heroku用起動設定
├── .streamlit/config.toml     # Streamlitテーマ設定
└── README_DEPLOY.md           # デプロイ手順
```

## デプロイ手順 (Streamlit Cloud)

1. **GitHubリポジトリ準備**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Streamlit Cloud設定**
   - https://share.streamlit.io/ にアクセス
   - 「New app」をクリック
   - リポジトリを選択
   - Main file path: `app/main.py`

3. **環境変数設定**
   - Advanced settings で環境変数を追加
   - または `.streamlit/secrets.toml` をGitHubにプッシュ

4. **デプロイ完了**
   - 自動ビルド・デプロイが実行されます
   - URLが生成され、アプリが公開されます

## トラブルシューティング

### よくある問題と解決方法

1. **ImportError**: 
   - `requirements.txt` にすべての依存関係が含まれているか確認

2. **Streamlit version conflicts**:
   - `requirements.txt` でバージョンを明示的に指定

3. **Environment variables not found**:
   - Streamlit Cloud の Advanced settings で環境変数が正しく設定されているか確認

4. **Path issues**:
   - `app/main.py` がメインファイルとして正しく指定されているか確認