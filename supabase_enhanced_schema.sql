-- Supabaseテーブル構造拡張案
-- ユーザーの学習進度とこってぃくんの状態を記録

-- 1. ユーザー学習統計テーブル
CREATE TABLE user_learning_stats (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    total_watch_time INTEGER DEFAULT 0, -- 総視聴時間（秒）
    total_videos INTEGER DEFAULT 0,     -- 視聴した動画数
    avg_comprehension FLOAT DEFAULT 0,  -- 平均理解度
    learning_streak INTEGER DEFAULT 0,  -- 連続学習日数
    skill_level TEXT DEFAULT 'beginner', -- 'beginner', 'intermediate', 'advanced'
    last_activity TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. 動画別ユーザー進度テーブル
CREATE TABLE user_video_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    video_id INTEGER,
    watch_count INTEGER DEFAULT 0,      -- 視聴回数
    total_watch_time INTEGER DEFAULT 0, -- この動画の総視聴時間
    best_comprehension INTEGER DEFAULT 0, -- 最高理解度
    favorite BOOLEAN DEFAULT false,     -- お気に入り
    notes TEXT,                        -- ユーザーノート
    last_watched TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. こってぃくん状態履歴テーブル
CREATE TABLE kotti_state_history (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    video_id INTEGER,
    stage INTEGER DEFAULT 1,           -- こってぃくんのステージ
    special_effects TEXT[],           -- 特殊エフェクトの配列
    size_bonus FLOAT DEFAULT 1.0,    -- サイズボーナス
    achievements TEXT[],              -- 獲得した実績
    emotion TEXT DEFAULT 'normal',    -- 感情状態
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. ユーザー実績テーブル
CREATE TABLE user_achievements (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    achievement_type TEXT NOT NULL,   -- 'streak_master', 'video_collector', etc.
    achievement_name TEXT NOT NULL,
    achievement_description TEXT,
    earned_at TIMESTAMP DEFAULT NOW(),
    is_displayed BOOLEAN DEFAULT false -- 表示済みフラグ
);

-- 5. 学習セッション記録テーブル
CREATE TABLE learning_sessions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    session_date DATE DEFAULT CURRENT_DATE,
    videos_watched INTEGER DEFAULT 0,
    total_time INTEGER DEFAULT 0,
    avg_comprehension FLOAT DEFAULT 0,
    session_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- インデックス作成（クエリ最適化）
CREATE INDEX idx_user_video_progress_user_id ON user_video_progress(user_id);
CREATE INDEX idx_user_video_progress_video_id ON user_video_progress(video_id);
CREATE INDEX idx_kotti_state_history_user_id ON kotti_state_history(user_id);
CREATE INDEX idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX idx_learning_sessions_user_date ON learning_sessions(user_id, session_date);

-- RLS（Row Level Security）設定
ALTER TABLE user_learning_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_video_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE kotti_state_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_sessions ENABLE ROW LEVEL SECURITY;

-- ユーザー自身のデータのみアクセス可能にする
CREATE POLICY "Users can view own learning stats" ON user_learning_stats FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own video progress" ON user_video_progress FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own kotti history" ON kotti_state_history FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own achievements" ON user_achievements FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own sessions" ON learning_sessions FOR ALL USING (auth.uid() = user_id);