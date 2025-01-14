import discord
import asyncio
import os
from dotenv import load_dotenv
from discord import Intents
from discord.enums import ChannelType
from discord.ext import commands

load_dotenv('.env')
token = os.getenv("TOKEN")

# ログを取得したいフォーラムチャンネルのID
FORUM_CHANNEL_ID = 1304042173938929725

# HTMLテンプレート
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <title>{thread_name} - Discord Logs</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width">
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #36393e; color: #dcddde; margin: 0; }}
        .message {{ padding: 10px; border-bottom: 1px solid #444; }}
        .author {{ font-weight: bold; color: #7289da; }}
        .content {{ margin-left: 10px; }}
        .timestamp {{ font-size: 0.8em; color: #aaa; }}
    </style>
</head>
<body>
    <h1>Thread: {thread_name}</h1>
    <div id="messages">
        {messages}
    </div>
</body>
</html>
"""

async def fetch_logs():
    # Discordクライアントの設定
    intents = discord.Intents.default()
    intents.messages = True
    intents.guilds = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'Logged in as {client.user}')
        guild = discord.utils.get(client.guilds)
        forum_channel = guild.get_channel(FORUM_CHANNEL_ID)

        if forum_channel is None or forum_channel.type != discord.ChannelType.forum:
            print(f"Forum channel with ID {FORUM_CHANNEL_ID} not found or is not a forum.")
            await client.close()
            return

        # 各スレッドのメッセージを取得
        for thread in forum_channel.threads:
            print(f"Fetching messages from thread: {thread.name}")

            messages_html = ""
            async for message in thread.history(limit=None):
                timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                messages_html += f"""
                <div class="message">
                    <span class="timestamp">{timestamp}</span>
                    <span class="author">{message.author}</span>:
                    <span class="content">{message.content}</span>
                </div>
                """

            # スレッドごとにHTMLファイルを作成
            thread_name_sanitized = thread.name.replace("/", "_")  # ファイル名に使える形に変換
            html_content = HTML_TEMPLATE.format(thread_name=thread.name, messages=messages_html)

            with open(f"{thread_name_sanitized}.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            print(f"Saved thread logs to {thread_name_sanitized}.html")

        await client.close()

    await client.start(token)

# メインイベントループ
asyncio.run(fetch_logs())
