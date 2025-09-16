import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

load_dotenv(".env")
token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="?",
    case_insensitive=True,
    intents=intents
)

@bot.event
async def on_ready():
    print(f'logined as {bot.user.name}')

# Cogs（機能別ファイル）を読み込む処理
async def load_cogs():
    # 'src/cogs' ディレクトリ内の.pyファイルをすべて探す
    for filename in os.listdir('./src/cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'{filename} を読み込みました。')
            except commands.ExtensionFailed as e:
                print(f'{filename} の読み込みに失敗しました: {e}')
            except commands.NoEntryPointError:
                print(f'Warning: {filename} does not have a setup function.')

# Botの実行
async def main():
    await load_cogs()
    await bot.start(token)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())