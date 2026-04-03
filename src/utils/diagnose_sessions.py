"""
DBに保存されたVCセッションを診断するスクリプト

データが減っているのか、表示時に減っているのかを調査します
"""

import asyncio
import os
import asyncpg

async def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL 環境変数が設定されていません")
        return

    conn = await asyncpg.connect(database_url)

    try:
        print("=" * 80)
        print("DBセッション診断")
        print("=" * 80)

        # 1. 総セッション数
        total = await conn.fetchval("SELECT COUNT(*) FROM vc_sessions")
        print(f"\n【1】総セッション数: {total}")

        # 2. 終了済みセッション数
        completed = await conn.fetchval(
            "SELECT COUNT(*) FROM vc_sessions WHERE left_time IS NOT NULL"
        )
        print(f"【2】終了済み（left_time ≠ NULL）: {completed}")

        # 3. 未終了セッション数
        uncompleted = await conn.fetchval(
            "SELECT COUNT(*) FROM vc_sessions WHERE left_time IS NULL"
        )
        print(f"【3】未終了（left_time = NULL）: {uncompleted}")

        # 4. ユーザー数
        users = await conn.fetchval("SELECT COUNT(*) FROM users")
        print(f"\n【4】総ユーザー数: {users}")

        # 5. セッションとユーザー数が一致しているか確認
        orphan_sessions = await conn.fetchval("""
            SELECT COUNT(*)
            FROM vc_sessions s
            LEFT JOIN users u ON s.user_id = u.user_id
            WHERE u.user_id IS NULL
        """)
        print(f"【5】ユーザー情報がないセッション: {orphan_sessions}")

        # 6. JOINで取得できるセッション数（users テーブルとの結合）
        joinable = await conn.fetchval("""
            SELECT COUNT(*)
            FROM vc_sessions s
            JOIN users u ON s.user_id = u.user_id
        """)
        print(f"【6】JOIN可能なセッション（users と結合可能）: {joinable}")

        # 7. 最新100件取得時の件数
        latest = await conn.fetchval("""
            SELECT COUNT(*)
            FROM (
                SELECT s.id
                FROM vc_sessions s
                JOIN users u ON s.user_id = u.user_id
                ORDER BY s.join_time DESC
                LIMIT 100
            ) AS subquery
        """)
        print(f"【7】最新100件の実際の件数: {latest}")

        # 8. 詳細分析
        print("\n" + "=" * 80)
        print("詳細分析")
        print("=" * 80)

        # チャンネル移動の可能性をチェック
        multi_sessions = await conn.fetch("""
            SELECT u.username, u.display_name, COUNT(*) as session_count,
                   MAX(s.join_time) as latest_join
            FROM vc_sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.left_time IS NULL
            GROUP BY u.user_id, u.username, u.display_name
            HAVING COUNT(*) > 1
        """)

        if multi_sessions:
            print(f"\n⚠️  複数の未終了セッションを持つユーザー:")
            for row in multi_sessions:
                print(f"  - {row['display_name'] or row['username']}: {row['session_count']}個")
        else:
            print(f"\n✓ 複数的な未終了セッションはありません")

        # 古いセッション（72時間以上）をチェック
        old_sessions = await conn.fetchval("""
            SELECT COUNT(*)
            FROM vc_sessions
            WHERE left_time IS NULL
              AND join_time < NOW() - INTERVAL '72 hours'
        """)
        print(f"\n古いセッション（72時間以上前に参加、未終了）: {old_sessions}")

        print("\n" + "=" * 80)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
