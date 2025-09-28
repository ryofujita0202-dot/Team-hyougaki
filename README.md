# Learning Fish Tank - SUPABASE統合版

<!-- 🌐 **ライブアプリ**: [https://team-hyougaki.streamlit.app/](https://team-hyougaki.streamlit.app/) -->
🌐 **ライブアプリ**: Streamlit Cloudでデプロイ準備中...

📂 **GitHubリポジトリ**: [https://github.com/ryofujita0202-dot/Team-hyougaki](https://github.com/ryofujita0202-dot/Team-hyougaki)

## 概要
動画学習を魚の育成ゲーム形式で管理するStreamlitアプリケーション。
SUPABASE認証・データベース統合により、学習データの永続化を実現。

**🐠 統合完了**: アプリ_こってぃの魚生成システムを統合し、より美しく多様な魚の生成が可能になりました。

## ✨ 主要機能

- 🎯 **5段階健康度システム**: 忘却曲線理論に基づく科学的な記憶管理
- 🐠 **こってぃくんの魚**: 健康度に応じて表情が変化する可愛い魚たち
- 👑 **金のこってぃくん**: 健康度95%以上で出現する特別な伝説の魚
- 📊 **学習記録**: 視聴回数・時間・理解度・メモの累積管理
- 🎮 **水槽アニメーション**: リアルタイムで泳ぐ魚の癒し系表示
- 🔄 **復習システム**: 最適なタイミングでの復習提案
- 📱 **レスポンシブUI**: PC・スマホどちらでも快適操作

## 🚀 セットアップ

### 1. 環境構築
```bash
cd "learning-fish-tank - Ver6"
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux  
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 環境変数設定
`.env` ファイルを作成し、以下を設定：
```env
# SUPABASE設定
SUPABASE_URL=your-supabase-project-url
SUPABASE_ANON_KEY=your-supabase-anon-key

# YouTube API（オプション）
YOUTUBE_API_KEY=your-youtube-api-key
```

### 3. SUPABASE設定
1. [supabase.com](https://supabase.com) でプロジェクト作成
2. SQL Editor で `db/schema.sql` を実行
3. Settings → Authentication で適切な設定を行う

詳細は `SUPABASE_INTEGRATION_GUIDE.md` を参照

## 🎮 起動方法

### 推奨方法（エラー回避）

#### Windows環境
1. **簡単起動（バッチファイル）**
   ```bash
   start_streamlit.bat
   ```
   プロジェクトフォルダの `start_streamlit.bat` をダブルクリックするか、コマンドプロンプトから実行

2. **PowerShell起動**
   ```powershell
   .\start_streamlit.ps1
   ```
   
3. **手動起動（確実な方法）**
   ```bash
   # 1. 仮想環境をアクティベート
   .venv\Scripts\activate
   
   # 2. Streamlitを起動
   streamlit run app\main.py
   ```

#### macOS/Linux環境
```bash
# 仮想環境をアクティベート
source .venv/bin/activate

# Streamlitを起動
streamlit run app/main.py
```

### トラブルシューティング
- **実行ポリシーエラー**: PowerShellで `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` を実行
- **パスエラー**: プロジェクトフォルダ内で実行しているか確認
- **Python環境エラー**: 仮想環境が正しくアクティベートされているか確認

## ✨ 主な機能

### 🐠 魚育成システム
- 動画視聴で魚が成長
- 忘却曲線による自動的な魚の状態変化
- リアルタイムアニメーション水槽

### 👪 親子アカウント機能
- 親アカウント：子の学習状況を監視
- 子アカウント：個別の魚育成と学習記録
- SUPABASE認証による安全な管理

### 📊 学習管理機能
- YouTube動画URLの自動解析
- 学習履歴の可視化
- 期限管理と復習提案

## 📁 プロジェクト構造
```
├── app/
│   ├── main.py              # メインアプリケーション
│   ├── lib/                 # コアライブラリ
│   └── assets/              # 画像アセット
├── views/
│   ├── parent_view.py       # 親ビュー
│   └── child_view.py        # 子ビュー
├── utils/
│   ├── config.py            # 設定管理
│   └── supabase_client.py   # SUPABASE統合
├── services/                # 外部APIクライアント
├── models/                  # データモデル
├── repositories/            # データアクセス層
└── db/
    └── schema.sql           # データベーススキーマ
```

## 🛠️ 技術スタック
- **フロントエンド**: Streamlit
- **バックエンド**: Python
- **データベース**: SUPABASE (PostgreSQL)
- **認証**: SUPABASE Auth
- **API**: YouTube Data API

## 📚 ドキュメント
- `SUPABASE_INTEGRATION_GUIDE.md` - SUPABASE統合の完全ガイド

## 🔧 開発・デバッグ
開発中にメール認証を無効化したい場合は、SUPABASE Dashboard で設定変更可能。
詳細は統合ガイドを参照してください。

## 📦 プロジェクト統合履歴
**2025/09/26**: アプリ_こってぃの魚生成システムを統合
- こってぃ版の動的魚生成アルゴリズムを`app/lib/dynamic_fish_generator.py`に統合
- 魚の画像リソース（`fffish.png`）を`app/assets/`に移動
- より多様で魅力的な魚の見た目生成が可能に
- アーカイブフォルダに元のサンプル画像とスクリプトを保存
>>>>>>> e03faefca1904db80c84fb186cb91ed7caa8a397
