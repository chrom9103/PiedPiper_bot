from datetime import datetime, timedelta, timezone
from collections import defaultdict
import glob
import re

# 計算対象講義を設定
lect = "08/17_20:00-22:00 【ストリングスの重ね方と打ち込み方】by ばんえつ"
pattern = "^(\d{2}/\d{2})_(\d{2}:\d{2})-(\d{2}:\d{2})\s【(.*?)】by\s(.*?)$"

match = re.search(pattern, lect)
print(match)

if match:
    print(match.group())
    print(match.group(1))
    date_str = match.group(1)
    start_time_str = match.group(2)
    end_time_str = match.group(3)
    title = match.group(4)

    # 年の情報を補完
    year = "2025"
    
    start_time_jst_str = f"{year}/{date_str}-{start_time_str}:00"
    end_time_jst_str = f"{year}/{date_str}-{end_time_str}:00"

    print(f"start_time_jst_str: {start_time_jst_str}")
    print(f"end_time_jst_str: {end_time_jst_str}")
else:
    print("パターンに一致する文字列が見つかりませんでした。")

# 計算対象の期間を日本標準時 (JST) で設定
JST = timezone(timedelta(hours=+9), 'JST')

# JSTからUTCへ変換
start_time_jst = datetime.strptime(start_time_jst_str, "%Y/%m/%d-%H:%M:%S").replace(tzinfo=JST)
end_time_jst = datetime.strptime(end_time_jst_str, "%Y/%m/%d-%H:%M:%S").replace(tzinfo=JST)

start_time_utc = start_time_jst.astimezone(timezone.utc)
end_time_utc = end_time_jst.astimezone(timezone.utc)

# ログファイルのパターン
file_pattern = './datas/vc_log_*.txt'
user_events = defaultdict(list)

# ファイルからログを読み込み
# ファイル名から年月を取得し、集計期間と関連があるか確認
for file_path in glob.glob(file_pattern):
    try:
        # ファイル名から年月（例: '2025-08'）を抽出
        file_year_month = file_path.split('_')[-1].split('.')[0]
        # 期間の年月と一致するか確認
        if file_year_month == start_time_utc.strftime('%Y-%m'):
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip().strip('[]')
                    if not line:
                        continue
                    try:
                        name, time_str, flag_str = line.split(',')
                        timestamp_utc = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                        flag = int(flag_str)
                        user_events[name].append((timestamp_utc, flag))

                    except ValueError as e:
                        print(f"Skipping malformed line in {file_path}: {line.strip()}. Error: {e}")
    except IndexError:
        print(f"Skipping file with unexpected name format: {file_path}")
        continue

# 各ユーザーの接続時間を計算
user_total_times = defaultdict(float)

for name, events in user_events.items():
    events.sort()
    
    join_time = None
    
    # 期間開始時点での接続状態を判断
    pre_start_events = [e for e in events if e[0] < start_time_utc]
    if pre_start_events:
        last_event_before_start = pre_start_events[-1]
        if last_event_before_start[1] == 0:
            join_time = start_time_utc

    # 期間中のイベントを処理
    for timestamp, flag in events:
        if flag == 0:  # 接続イベント
            if start_time_utc <= timestamp <= end_time_utc:
                if join_time is None:
                    join_time = timestamp
        
        elif flag == 1:  # 切断イベント
            if join_time is not None:
                if start_time_utc <= timestamp <= end_time_utc:
                    delta = timestamp - join_time
                    user_total_times[name] += delta.total_seconds()
                    join_time = None
                elif timestamp > end_time_utc and join_time < end_time_utc:
                    delta = end_time_utc - join_time
                    user_total_times[name] += delta.total_seconds()
                    join_time = None

    # 期間終了時にまだ接続していた場合の処理
    if join_time is not None and join_time < end_time_utc:
        delta = end_time_utc - join_time
        user_total_times[name] += delta.total_seconds()

# 結果を出力用に整形し、接続時間の降順にソート
result_array = sorted(
    [(name, int(round(seconds))) for name, seconds in user_total_times.items()],
    key=lambda x: x[1],
    reverse=True
)

# 最終結果を出力
print("---")
print("集計結果")
print(f"講座名: {title}")
print(f"対象期間 (JST): {start_time_jst_str} - {end_time_jst_str}")
print(f"対象期間 (UTC): {start_time_utc.strftime('%Y/%m/%d-%H:%M:%S')} - {end_time_utc.strftime('%Y/%m/%d-%H:%M:%S')}")
print("---")
if not result_array:
    print("指定された期間内にVCへの接続はありませんでした。")
else:
    for name, seconds in result_array:
        minutes = seconds // 60
        hours = minutes // 60
        minutes_remaining = minutes % 60
        print(f"ユーザー: {name:<10} | 接続時間: {seconds}秒 ({hours}時間 {minutes_remaining}分)")