import asyncio
import os
import re
from datetime import datetime, timedelta, timezone

import asyncpg

# 計算対象講義を設定
lect = """
08/01_20:00~21:30
ゆるたるとラジオ #1「Digitart史談義 ～老人会～」
by くろむ, ロロ, くしらっちょ, Sora_339
"""
pattern = (
    r"^(?P<date>\d{2}/\d{2})_(?P<start>\d{1,2}:\d{2})~(?P<end>\d{1,2}:\d{2})\s*\n"
    r"(?P<title>[^\n]+)\n"
    r"(?:(?P<description>.*?)\n)?"
    r"by\s+(?P<organizer>[^\n]+)\s*$"
)
year = "2026"
JST = timezone(timedelta(hours=9), "JST")

match = re.fullmatch(pattern, lect.strip(), flags=re.DOTALL)
if not match:
    raise ValueError(f"講義情報の形式が不正です: {lect}")

date_str = match.group("date")
start_time_str = match.group("start")
end_time_str = match.group("end")
title = match.group("title")


def parse_extended_datetime(date_str, time_str):
    """24:00以降の時刻を翌日以降へ繰り上げて日時に変換する。"""
    try:
        base_date = datetime.strptime(f"{year}/{date_str}", "%Y/%m/%d").replace(tzinfo=JST)
        hour_str, minute_str = time_str.split(":")
        hour = int(hour_str)
        minute = int(minute_str)
    except (ValueError, TypeError) as error:
        raise ValueError(f"日付または時刻の形式が不正です: {date_str} {time_str}") from error

    if not 0 <= hour <= 47 or not 0 <= minute <= 59:
        raise ValueError(f"時刻は00:00から47:59の範囲で指定してください: {time_str}")

    return base_date + timedelta(hours=hour, minutes=minute)


start_time_jst = parse_extended_datetime(date_str, start_time_str)
end_time_jst = parse_extended_datetime(date_str, end_time_str)
if end_time_jst <= start_time_jst:
    raise ValueError("終了時刻は開始時刻より後に指定してください")

start_time_jst_str = start_time_jst.strftime("%Y/%m/%d-%H:%M:%S")
end_time_jst_str = end_time_jst.strftime("%Y/%m/%d-%H:%M:%S")
start_time_utc = start_time_jst.astimezone(timezone.utc)
end_time_utc = end_time_jst.astimezone(timezone.utc)


async def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL 環境変数が設定されていません")

    conn = await asyncpg.connect(database_url)
    try:
        rows = await conn.fetch("""
            SELECT u.username,
                   u.display_name,
                   SUM(EXTRACT(EPOCH FROM (
                       LEAST(COALESCE(s.left_time, $2), $2)
                       - GREATEST(s.join_time, $1)
                   ))) AS total_seconds
            FROM vc_sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.join_time < $2
              AND (s.left_time IS NULL OR s.left_time > $1)
            GROUP BY u.user_id, u.username, u.display_name
            ORDER BY total_seconds DESC
        """, start_time_utc, end_time_utc)
    finally:
        await conn.close()

    result_array = [
        (row["display_name"] or row["username"], int(round(row["total_seconds"])))
        for row in rows
    ]

    print("---")
    print("集計結果")
    print(f"講座名: {title}")
    print(f"対象期間 (JST): {start_time_jst_str} - {end_time_jst_str}")
    print(f"対象期間 (UTC): {start_time_utc.strftime('%Y/%m/%d-%H:%M:%S')} - {end_time_utc.strftime('%Y/%m/%d-%H:%M:%S')}")
    print("---")
    if not result_array:
        print("指定された期間内にVCへの接続はありませんでした。")
        return

    for name, seconds in result_array:
        minutes = seconds // 60
        hours = minutes // 60
        minutes_remaining = minutes % 60
        print(f"ユーザー: {name:<10} | 接続時間: {seconds}秒 ({hours}時間 {minutes_remaining}分)")


if __name__ == "__main__":
    asyncio.run(main())