-- ユーザーマスタ（Discord User ID で管理）
CREATE TABLE IF NOT EXISTS users (
    user_id       BIGINT PRIMARY KEY,          -- Discord User ID (snowflake)
    username      VARCHAR(64) NOT NULL,        -- 最新のユーザー名
    display_name  VARCHAR(128),                -- 最新の表示名
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- VCセッション（1行 = 1回の接続）
CREATE TABLE IF NOT EXISTS vc_sessions (
    id            SERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES users(user_id),
    guild_id      BIGINT NOT NULL,             -- サーバーID
    channel_id    BIGINT NOT NULL,             -- VCチャンネルID
    join_time     TIMESTAMP WITH TIME ZONE NOT NULL,
    left_time     TIMESTAMP WITH TIME ZONE,    -- NULL = 現在接続中
    duration_sec  INTEGER GENERATED ALWAYS AS (
        CASE WHEN left_time IS NOT NULL
             THEN EXTRACT(EPOCH FROM (left_time - join_time))::INTEGER
             ELSE NULL
        END
    ) STORED
);

-- クエリ高速化用インデックス
CREATE INDEX idx_sessions_user_time ON vc_sessions(user_id, join_time, left_time);
CREATE INDEX idx_sessions_time_range ON vc_sessions(join_time, left_time);
CREATE INDEX idx_sessions_guild ON vc_sessions(guild_id, join_time);
