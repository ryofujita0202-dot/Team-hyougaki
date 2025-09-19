いいね！素案をベースに、初見の開発者でも迷わず動かせる実用的なREADMEに整えました。
（そのまま `README.md` に貼り付けて使えます）

---

# GyoLog（ギョログ）

学習の“泳跡”を残す、育成型ラーニングログアプリ 🐟

> **学んだ動画を記録 → 自動要約（Wikipedia＋AI） → ログ化 → 育成要素（魚が育つ）**
> 学びを「見える化」して、継続をゲーム感覚で後押しします。

---

## プロジェクト概要

* **目的**：学んだトピックの動画（YouTube）を記録し、Wikipedia要約とAI要約を自動添付して“学びの痕跡”を残す。
* **開発期間**：2025/09/16 – 2025/09/29（2週間）
* **ターゲット**：

  * 親子学習（親＝管理・見守り／子＝学習＆記録）
  * 自主学習者・研修受講者・社内勉強会の参加者

---

## 主要機能（Phase 1）

* [x] YouTube動画URLの登録・メタ情報取得（タイトル／チャンネル／再生時間）
* [x] Wikipediaから関連要約を自動添付
* [x] Gemini（Google AI Studio）で「要点・3行要約・章立て」を生成
* [x] 学習ログの保存・一覧表示（検索・フィルタ）
* [x] 親ビュー／子ビューの切替（権限分離）
* [x] “育成要素”：学習量に応じて**金魚が育つ**（視聴時間・本数・連続学習日数で成長）

> **Phase 2候補**：学習クエスト／実績バッジ／視聴完了検知（YouTube IFrame API）／コピー用レポート出力（Markdown/PDF）

---

## 技術スタック

* **フロントエンド**：Streamlit
* **バックエンド**：YouTube Data API / Google APIs / Google AI Studio（Gemini）
* **データベース**：Supabase（PostgreSQL + Auth + Storage）
* **言語**：Python 3.10+
* **その他**：Requests / Pydantic / python-dotenv

---

## チーム体制

* **班長**：こってぃ
* **班員**：たけさん、りょうちゃん

---

## ファイル構成

```
team-hyougaki/
├── app.py                     # メインアプリ（ルーティング／画面切替）
├── init_db.py                 # DB初期化スクリプト（テーブル作成）
├── user_utils.py              # 認証・ユーザー関連（Supabase Auth連携）
├── parent_view.py             # 親用画面UI
├── child_view.py              # 子用画面UI
├── services/
│   ├── youtube_client.py      # YouTube APIクライアント
│   ├── wiki_client.py         # Wikipedia要約取得
│   └── gemini_client.py       # Gemini要約生成
├── models/
│   └── schemas.py             # Pydanticスキーマ
├── requirements.txt           # 依存パッケージ
├── .env.example               # 環境変数サンプル
├── .gitignore                 # 機密・生成物を除外
├── data/                      # 一時データ（※DBはSupabase）
└── docs/
    └── requirements_definition.md  # 要件定義
```

---

## セットアップ

### 必要環境

* Python **3.10以上**
* Git
* Google Cloud アカウント（YouTube Data API 有効化）
* Google AI Studio（Gemini API キー）
* Supabase プロジェクト（DB & Auth）

### 1) リポジトリ取得

```bash
git clone <リポジトリURL>
cd team-hyougaki
```

### 2) 仮想環境

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3) 依存関係

```bash
pip install -r requirements.txt
```

### 4) 環境変数

```bash
cp .env.example .env
# .envを開き、各キーを入力
```

`.env` に設定する値（例）：

| 変数名                        | 説明                             |
| -------------------------- | ------------------------------ |
| `OPENAI_API_KEY`           | （未使用なら空でOK）                    |
| `GOOGLE_AI_STUDIO_API_KEY` | GeminiのAPIキー（Google AI Studio） |
| `YOUTUBE_API_KEY`          | YouTube Data API v3のAPIキー      |
| `SUPABASE_URL`             | SupabaseプロジェクトURL              |
| `SUPABASE_ANON_KEY`        | Supabase匿名キー（フロント用）            |
| `APP_ENV`                  | `local` / `dev` / `prod`       |
| `WIKI_LANG`                | `ja`（Wikipedia参照言語）            |

> **注意**：`.env` と `*.secret.*` は絶対にコミットしないでください。

### 5) アプリ起動

```bash
streamlit run app.py
```

* 既定ポートは `8501`。使用中の場合は `--server.port 8502` などを指定。

---

## 使い方（ユーザーフロー）

1. **ログイン**（親／子を選択）
2. **動画を登録**：YouTube URLを貼付 → APIでメタ情報取得
3. **要約付与**：Wikipedia要約を取得、Geminiで「要点／3行要約／章立て／引用秒範囲」を生成
4. **保存**：学習ログに記録、一覧で検索・絞り込み
5. **魚が育つ**：

   * 本数・視聴時間・連続日数に応じてサイズやアニメーションが変化
   * 宿題（クエスト）達成でポイント＆バッジ付与

---

## 画面構成

* **子ビュー（child\_view）**：
  学習登録／ログ一覧／マイ実績・バッジ／“金魚の成長”可視化
* **親ビュー（parent\_view）**：
  進捗ダッシュボード／フィルタ（期間・カテゴリ）／個別ログ閲覧／クエスト配布

---

## アーキテクチャ概要

```
[Streamlit UI]
   ├─ child_view / parent_view
   │
   ├─ services/
   │   ├─ youtube_client  ──> YouTube Data API
   │   ├─ wiki_client     ──> Wikipedia (lang=ja)
   │   └─ gemini_client   ──> Google AI Studio (Gemini)
   │
   └─ Supabase (Auth + PostgreSQL + Storage)
          ↑ 認証/CRUD
```

---

## データモデル（抜粋）

| モデル                 | 用途                          |
| ------------------- | --------------------------- |
| **User（app\_user）** | 親・子の識別、表示名、権限               |
| **Quest**           | 学習タスク（任意・宿題）                |
| **QuestExecution**  | 学習実績（YouTubeメタ、Wiki要約、AI要約） |
| **Reward**          | ポイント履歴                      |
| **Achievement**     | バッジ・実績                      |

---

## 開発ルール

### ブランチ戦略

* `main`：本番／安定
* `feature/<owner>/<feature>`：機能開発
  例）`feature/kotty/quest-create`, `feature/take/log-list`

### コミット規約（日本語OK）

* 形式：`[種別] 変更内容`
* 例：`[add] クエスト作成画面`, `[fix] ログイン処理のバグ`

**種別の例**：add / fix / refactor / perf / docs / chore / test

### PR・レビュー

* PRには**1人以上の承認**が必要
* コメントは**全て解決**してからマージ
* 機能が**小さくまとまったら即PR**（早めに共有）

---

## Phase 1 タスク分担（案）

* 情報設計／UI設計／親ビュー（ダッシュボード・フィルタ）
* YouTube & Wiki連携／要約生成（Gemini）／サービス層
* Supabaseスキーマ／認証連携／子ビュー（登録・一覧・育成表示）

