"""
PostgreSQL データベース接続・操作モジュール
VCセッションの記録と集計を担当する
"""

import os
import asyncpg
from datetime import datetime, timezone


class Database:
    """asyncpg ベースの非同期DBクライアント"""

    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        """コネクションプールを作成し、テーブルが存在しなければ作成する"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL 環境変数が設定されていません")

        self.pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=5,
        )
        await self._ensure_tables()
        print("Database connected.")

    async def close(self):
        """コネクションプールを閉じる"""
        if self.pool:
            await self.pool.close()
            print("Database connection closed.")

    # ------------------------------------------------------------------
    # テーブル初期化
    # ------------------------------------------------------------------
    async def _ensure_tables(self):
        """テーブルとインデックスが存在しなければ作成する"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id       BIGINT PRIMARY KEY,
                    username      VARCHAR(64) NOT NULL,
                    display_name  VARCHAR(128),
                    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS vc_sessions (
                    id            SERIAL PRIMARY KEY,
                    user_id       BIGINT NOT NULL REFERENCES users(user_id),
                    guild_id      BIGINT NOT NULL,
                    channel_id    BIGINT NOT NULL,
                    join_time     TIMESTAMP WITH TIME ZONE NOT NULL,
                    left_time     TIMESTAMP WITH TIME ZONE,
                    duration_sec  INTEGER GENERATED ALWAYS AS (
                        CASE WHEN left_time IS NOT NULL
                             THEN EXTRACT(EPOCH FROM (left_time - join_time))::INTEGER
                             ELSE NULL
                        END
                    ) STORED
                );
            """)
            # インデックスを作成 (IF NOT EXISTS)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_user_time
                    ON vc_sessions(user_id, join_time, left_time);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_time_range
                    ON vc_sessions(join_time, left_time);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_guild
                    ON vc_sessions(guild_id, join_time);
            """)

    # ------------------------------------------------------------------
    # ユーザー管理
    # ------------------------------------------------------------------
    async def upsert_user(self, user_id: int, username: str, display_name: str | None = None):
        """ユーザー情報を挿入または更新する"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username, display_name, updated_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (user_id) DO UPDATE
                    SET username     = EXCLUDED.username,
                        display_name = EXCLUDED.display_name,
                        updated_at   = NOW()
            """, user_id, username, display_name)

    # ------------------------------------------------------------------
    # VCセッション操作
    # ------------------------------------------------------------------
    async def open_session(
        self, user_id: int, guild_id: int, channel_id: int, join_time: datetime
    ) -> int:
        """VC参加時にセッションを開始する。セッションIDを返す。"""
        async with self.pool.acquire() as conn:
            session_id = await conn.fetchval("""
                INSERT INTO vc_sessions (user_id, guild_id, channel_id, join_time)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, user_id, guild_id, channel_id, join_time)
            return session_id

    async def close_session(self, user_id: int, guild_id: int, left_time: datetime) -> bool:
        """VC退出時にセッションを閉じる。更新できたかどうかを返す。"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE vc_sessions
                SET left_time = $1
                WHERE id = (
                    SELECT id FROM vc_sessions
                    WHERE user_id = $2
                      AND guild_id = $3
                      AND left_time IS NULL
                    ORDER BY join_time DESC
                    LIMIT 1
                )
            """, left_time, user_id, guild_id)
            # result は "UPDATE N" 形式の文字列
            return result == "UPDATE 1"

    async def close_stale_sessions(self, close_time: datetime | None = None):
        """Bot起動時に閉じられていないセッションを強制終了する"""
        if close_time is None:
            close_time = datetime.now(timezone.utc)
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE vc_sessions
                SET left_time = $1
                WHERE left_time IS NULL
            """, close_time)
            count = int(result.split()[-1])
            if count > 0:
                print(f"Closed {count} stale VC session(s).")

    # ------------------------------------------------------------------
    # 集計クエリ
    # ------------------------------------------------------------------
    async def get_user_total_time(
        self, user_id: int, start_time: datetime, end_time: datetime
    ) -> int:
        """特定期間におけるユーザーの累計VC接続時間(秒)を返す"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT COALESCE(SUM(duration_sec), 0)
                FROM vc_sessions
                WHERE user_id = $1
                  AND join_time >= $2
                  AND join_time < $3
                  AND left_time IS NOT NULL
            """, user_id, start_time, end_time)
            return result

    async def get_users_at_time(
        self, target_time: datetime, guild_id: int
    ) -> list[asyncpg.Record]:
        """特定の時刻に接続していたユーザー一覧を返す"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT u.user_id, u.username, u.display_name,
                       s.channel_id, s.join_time, s.left_time
                FROM vc_sessions s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.guild_id = $1
                  AND s.join_time <= $2
                  AND (s.left_time > $2 OR s.left_time IS NULL)
            """, guild_id, target_time)
            return rows

    async def get_ranking(
        self, guild_id: int, start_time: datetime, end_time: datetime, limit: int = 20
    ) -> list[asyncpg.Record]:
        """特定期間のVC接続時間ランキングを返す"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT u.user_id, u.username, u.display_name,
                       SUM(s.duration_sec) AS total_seconds
                FROM vc_sessions s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.guild_id = $1
                  AND s.join_time >= $2
                  AND s.join_time < $3
                  AND s.left_time IS NOT NULL
                GROUP BY u.user_id, u.username, u.display_name
                ORDER BY total_seconds DESC
                LIMIT $4
            """, guild_id, start_time, end_time, limit)
            return rows

    async def get_latest_sessions(self, limit: int = 100) -> list[asyncpg.Record]:
        """最新のVCセッション記録を取得する（デフォルト100件）"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT u.user_id, u.username, u.display_name,
                       s.id, s.guild_id, s.channel_id,
                       s.join_time, s.left_time, s.duration_sec
                FROM vc_sessions s
                JOIN users u ON s.user_id = u.user_id
                ORDER BY s.join_time DESC
                LIMIT $1
            """, limit)
            return rows


# グローバルシングルトン
db = Database()
