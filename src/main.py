import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv(".env")
token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='?', intents=intents)

@bot.event
async def on_ready():
    print(f'logined as {bot.user.name}')

# Cogs（機能別ファイル）を読み込む処理
async def load_cogs():
    # 'src/cogs' ディレクトリ内の.pyファイルをすべて探す
    for filename in os.listdir('./src/cogs'):
        if filename.endswith('.py'):
            # `.py` は不要なので取り除く
            await bot.load_extension(f'src.cogs.{filename[:-3]}')
            print(f'{filename} を読み込みました。')

# Botの実行
async def main():
    await load_cogs()
    await bot.start(token)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())