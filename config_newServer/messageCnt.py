import discord
import asyncio
from collections import defaultdict
import os
from dotenv import load_dotenv

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
        print(f'Logged in as {client.user}')
        guild = discord.utils.get(client.guilds)  # 最初のサーバーを取得

        if not guild:
            print("No guilds found.")
            await client.close()
            return

        print(f"Fetching message counts for guild: {guild.name}")
        user_message_count = defaultdict(int)  # 各ユーザーの発言数を記録

        # サーバー内の全テキストチャンネルを処理
        for channel in guild.text_channels:
            print(f"Processing channel: {channel.name}")
            try:
                # チャンネルのメッセージをカウント
                async for message in channel.history(limit=None):
                    user_message_count[message.author] += 1

                for thread in channel.threads:
                    print(f"  Processing thread: {thread.name}")
                    async for message in thread.history(limit=None):
                        user_message_count[message.author] += 1

            except discord.Forbidden:
                print(f"Permission denied for channel: {channel.name}")
            except Exception as e:
                print(f"Error processing channel {channel.name}: {e}")

        # サーバー全体の発言数を出力
        print("Total message counts per user:")
        for user, count in sorted(user_message_count.items(), key=lambda x: x[1], reverse=True):
            print(f"{user}: {count} messages")

        await client.close()
 
    await client.start(token)

# メインイベントループ
asyncio.run(fetch_message_counts())
