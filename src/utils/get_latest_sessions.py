"""
PostgreSQL上のvc_sessionsテーブルから、
最新100件のVC接続記録を生データとして出力するスクリプト

使用方法:
  DATABASE_URL="postgresql://digitart-bot:password@localhost:5432/digitart-bot" python src/utils/get_latest_sessions.py
  
  limitを指定する場合:
  DATABASE_URL="..." python src/utils/get_latest_sessions.py --limit 50
"""

import asyncio
import os
import asyncpg
import sys

async def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL 環境変数が設定されていません")
        print('例: DATABASE_URL="postgresql://digitart-bot:password@localhost:5432/digitart-bot" python src/utils/get_latest_sessions.py')
        return

    # コマンドオプションから limit を取得
    limit = 100
    if "--limit" in sys.argv:
        try:
            idx = sys.argv.index("--limit")
            limit = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Warning: --limit の値が不正です。デフォルトの100件を使用します。")

    conn = await asyncpg.connect(database_url)

    try:
        rows = await conn.fetch("""
            SELECT s.id, s.user_id, s.guild_id, s.channel_id,
                   s.join_time, s.left_time, s.duration_sec,
                   u.user_id, u.username, u.display_name, u.updated_at
            FROM vc_sessions s
            JOIN users u ON s.user_id = u.user_id
            ORDER BY s.join_time DESC
            LIMIT $1
        """, limit)

        if not rows:
            print("VCセッション記録がありません。")
            return

        for row in rows:
            print(row)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
