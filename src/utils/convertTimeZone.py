import pandas as pd
from io import StringIO

data = """

"""
df = pd.read_csv(StringIO(data), header=None, names=['user_id', 'timestamp', 'value'])
df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC').dt.tz_convert('Asia/Tokyo')
print(df)