from datetime import datetime
from collections import defaultdict
import glob
import os

# ファイルパスのパターン
file_pattern = './datas/vc_log_*.txt'
user_events = defaultdict(list)

# 複数ファイルを取得
for file_path in glob.glob(file_pattern):
    print(f"Processing file: {file_path}")
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip().strip('[]')
            if not line:
                continue
            name, time_str, flag = line.split(',')
            timestamp = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            user_events[name].append((timestamp, int(flag)))

# 接続時間を集計
user_total_times = {}

for name, events in user_events.items():
    events.sort()  # 時間順に並べ替え
    total_time = 0
    join_time = None

    for timestamp, flag in events:
        if flag == 0:  # join
            join_time = timestamp
        elif flag == 1 and join_time:
            delta = timestamp - join_time
            total_time += delta.total_seconds()
            join_time = None

    user_total_times[name] = total_time

# ソート用配列に変換して降順にソート
result_array = sorted(
    [(name, int(seconds)) for name, seconds in user_total_times.items()],
    key=lambda x: x[1],
    reverse=True
)

# 出力（任意）
for name, seconds in result_array:
    minutes = seconds // 60
    print(f"{name}: {seconds}秒 ({minutes}分)")
