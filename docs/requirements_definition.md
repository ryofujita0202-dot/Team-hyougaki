# お手伝いクエスト型お小遣いアプリ – 要件定義書
最終更新: 2025-09-20 / 版: v1.0 / 作成: team1_3peace

## 目次
- [1. プロジェクト概要](#1-プロジェクト概要)
- [2. ユーザー・ペイン・提供価値](#2-ユーザーペイン提供価値)
- [3. ユースケース](#3-ユースケース)
- [4. 機能要件](#4-機能要件)
- [5. 非機能要件](#5-非機能要件)
- [6. 画面要件（MVP）](#6-画面要件mvp)
- [7. データモデル（Supabase）](#7-データモデルsupabase)
- [8. 外部連携 / 依存](#8-外部連携--依存)
- [9. セキュリティ・運用](#9-セキュリティ運用)
- [10. 受け入れ基準](#10-受け入れ基準)
- [変更履歴](#変更履歴)

---

## 1. プロジェクト概要
- **プロダクト名**: お手伝いクエスト型お小遣いアプリ（仮）
- **目的**: 家庭内のお手伝いを “クエスト化” し、学びと報酬を可視化。視聴学習（YouTube）も合わせて記録・要約化。
- **期間**: 2025/09/16–2025/09/29（2週間PoC）
- **対象**: モバイルWeb中心（PCでも可）
- **技術**: Streamlit（フロント） / Python（バックエンド）/ YouTube API / Google STT + Gemini 2.5 Flash / Supabase（Auth + DB）

## 2. ユーザー・ペイン・提供価値
- **WHO**: 低学年の子どもを持つ保護者と子ども
- **ペイン**
  - 子どもが家事に前向きになりにくい / 継続しない
  - 学び（動画視聴）の中身が保護者から見えにくい
- **提供価値**
  - お手伝いタスクを“クエスト”として楽しく継続
  - 学習ログ（視聴→文字起こし→要約）で学びの見える化
  - 成長メタファ（魚のレベル/サイズ）でモチベ維持

## 3. ユースケース
1. **検索→視聴**：子がテーマを検索し動画を視聴。終了イベントを取得。
2. **要約生成**：音声→STT→Gemini要約（要点/3行/章立て/引用範囲）。
3. **評価・メモ**：★1–5＋自由メモ（Nano Bananaで短文整形）。
4. **お手伝いクエスト**：保護者がタスクを登録→子が達成報告→承認→報酬反映。
5. **可視化**：累計視聴・連続日数・達成数に応じて “魚” が成長。

## 4. 機能要件
- **検索/視聴**
  - YouTube検索結果（上位N件）をカード表示（タイトル/チャンネル/再生時間/サムネ/再生）。
  - IFrame Player APIの `onStateChange(ENDED)` を取得。
- **要約**
  - Google STT → Gemini 2.5 Flashで要約JSON生成  
    - `points[≤5]`, `three_lines[≤3]`, `chapters[≤5]`, `quotes[{start,end}]`
- **評価入力**
  - ★1–5、メモ（100–300字へ“Nano Banana”整形オプション）。
- **学習レベル**
  - `level_raw = α*総視聴分 + β*視聴回数 + γ*連続日数`（既定 α=1.0, β=2.0, γ=1.5）  
  - `level = clamp(floor(level_raw/scale),1,100)`（scale=10）
  - 魚サイズ：`min(100, 20 + level*0.8)%`
- **クエスト**
  - 登録/受注/達成報告/承認/履歴（MUSTは登録～承認まで）
- **保存**
  - Supabaseへ視聴リスト、視聴日時、要約JSON、評価、回数、サムネURL、クエスト進捗を保存
  - RLS有効化、AuthユーザーIDと突合

## 5. 非機能要件
- **性能**：検索→一覧 ≤ 2s（API待ち除く）、要約 ≤ 15s（ローディング表示）
- **可用性**：要約失敗時でも “視聴＋評価＋メモ” は保存継続
- **ログ**：API失敗/要約失敗/承認イベントを記録
- **プライバシー**：音声は処理後破棄・学習テキストは非公開が既定

## 6. 画面要件（MVP）
- **一覧**：検索ボックス、結果カード（再生・保存）
- **視聴/要約**：プレイヤー／要点・3行・章立て／評価・メモ
- **クエスト**：一覧/登録/承認
- **ダッシュボード**：総視聴時間・回数・連続日数・魚サイズ

## 7. データモデル（Supabase）
```sql
-- ユーザー
create table app_user(
  id uuid primary key default gen_random_uuid(),
  auth_user_id uuid unique not null,
  role text check (role in ('parent','child')),
  display_name text,
  family_id uuid,
  created_at timestamptz default now()
);

-- 視聴ログ
create table view_log(
  id uuid primary key default gen_random_uuid(),
  user_id uuid references app_user(id),
  video_id text not null,
  watched_at timestamptz default now(),
  watch_seconds int,
  rating int check (rating between 1 and 5),
  note text,
  summary_json jsonb,
  thumbnail_url text,
  view_count_accum int default 1
);

-- クエスト
create table quest(
  id uuid primary key default gen_random_uuid(),
  family_id uuid,
  title text not null,
  reward int not null,
  status text check (status in ('open','claimed','done','approved')) default 'open',
  created_at timestamptz default now()
);

-- RLSは user_id = auth.uid() を基本とし、parentは family_id で子を閲覧可能に
````

## 8. 外部連携 / 依存

* **YouTube Data API**：`search.list`, `videos.list`（字幕は `captions.download` があれば利用）
* **音声抽出**：サーバー側で `yt-dlp` 等 → 一時ファイルは処理後削除
* **Google STT**：`ja-JP`、必要に応じて長尺は非同期
* **Gemini 2.5 Flash**：要約JSON + Nano Banana整形
* **Supabase**：Auth + Postgres（RLS必須）+ Storage（任意）

## 9. セキュリティ・運用

* `.env` 管理：`GOOGLE_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`（クライアント露出禁止の鍵はサーバ側に）
* HTTPS必須、秘密情報はログに出さない
* APIクォータ監視、要約失敗の再試行（最大2回）

## 10. 受け入れ基準

* [ ] 検索→結果10件以上表示（タイトル/サムネ/再生時間）
* [ ] 視聴終了で評価・メモ入力→保存できる
* [ ] STT→要約→一覧サマリ反映
* [ ] 同一動画を2回視聴で回数=2、レベルが増加
* [ ] RLSにより他ユーザーのデータ非表示
* [ ] クエスト登録→達成報告→承認が通る
* [ ] 魚サイズがレベルに応じて変化

## 変更履歴

* v1.0 (2025-09-20): 初版作成

````

READMEからのリンク例：
```md
- 要件定義 → [docs/requirements_definition.md](./docs/requirements_definition.md)
````

