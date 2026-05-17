"""
PostgreSQL上のvc_sessionsテーブルから、
指定期間のVC接続時間を集計してコンソールに出力するスクリプト

使用方法:
  1. 下記の START_DATE / END_DATE を変更
  2. DATABASE_URL 環境変数を設定して実行
     例: DATABASE_URL="postgresql://digitart-bot:password@localhost:5432/digitart-bot" python src/utils/calcVCtime.py
"""

import asyncio
import os
import asyncpg
from datetime import datetime, timezone

# ========== 集計期間の設定 ==========
# 開始日時 (UTC)
START_DATE = datetime(2025, 4, 1, tzinfo=timezone.utc)
# 終了日時 (UTC) — この日時は含まない
END_DATE = datetime(2026, 5, 1, tzinfo=timezone.utc)
# ====================================


async def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL 環境変数が設定されていません")
        print('例: DATABASE_URL="postgresql://digitart-bot:password@localhost:5432/digitart-bot" python src/utils/calcVCtime.py')
        return

    conn = await asyncpg.connect(database_url)

    try:
        print(f"集計期間: {START_DATE.strftime('%Y-%m-%d %H:%M:%S')} ~ {END_DATE.strftime('%Y-%m-%d %H:%M:%S')} (UTC)")
        print("=" * 50)

        rows = await conn.fetch("""
            SELECT u.username, u.display_name,
                   SUM(s.duration_sec) AS total_seconds
            FROM vc_sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.join_time >= $1
              AND s.join_time < $2
              AND s.left_time IS NOT NULL
            GROUP BY u.user_id, u.username, u.display_name
            ORDER BY total_seconds DESC
        """, START_DATE, END_DATE)

        if not rows:
            print("該当期間のデータがありません。")
            return

        total_seconds_all = sum(row["total_seconds"] for row in rows)
        total_hours = total_seconds_all // 3600
        total_minutes = (total_seconds_all % 3600) // 60
        print(f"全メンバー合計: {total_seconds_all}秒 ({total_hours}時間{total_minutes}分)")
        print("-" * 50)

        for row in rows:
            seconds = row["total_seconds"]
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            name = row["display_name"] or row["username"]
            print(f"{name}: {seconds}秒 ({hours}時間{minutes}分)")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
