import discord
import asyncio
from collections import defaultdict
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Botのトークンを環境変数から取得
load_dotenv('.env')
token = os.getenv("TOKEN")

async def fetch_message_counts():
    # Discordクライアントの設定
    intents = discord.Intents.default()
    intents.messages = True
    intents.guilds = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print("Cleared to take off!")
        guild = discord.utils.get(client.guilds)  # 最初のサーバーを取得

        if not guild:
            print("No guilds found.")
            await client.close()
            return

        print(f"Fetching message counts for guild: {guild.name}")
        user_message_count = defaultdict(int)  # 各ユーザーの発言数を記録
        
        jst = timezone(timedelta(hours=9))
        start_date = datetime(2024, 4, 1, tzinfo=jst)

        for channel in guild.text_channels:
            print(f"Processing channel: {channel.name}")
            try:
                async for message in channel.history(limit=None):
                    if message.created_at.astimezone(jst) >= start_date:
                        user_message_count[message.author] += 1
            except discord.Forbidden:
                print(f"Permission denied for channel: {channel.name}")
            except Exception as e:
                print(f"Error processing channel {channel.name}: {e}")

        for thread in guild.threads:
            print(f"Processing thread: {thread.name}")
            try:
                async for message in thread.history(limit=None):
                    if message.created_at.astimezone(jst) >= start_date:
                        user_message_count[message.author] += 1

            except discord.Forbidden:
                print(f"Permission denied for Thread: {channel.name}")
            except Exception as e:
                print(f"Error processing thread {channel.name}: {e}")


        # サーバー全体の発言数を出力
        print("Total message counts per user:")
        for user, count in sorted(user_message_count.items(), key=lambda x: x[1], reverse=True):
            print(f"{user}: {count} messages")

        await client.close()
 
    await client.start(token)

# メインイベントループ
asyncio.run(fetch_message_counts())
