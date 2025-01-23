import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import random
import re

intents = discord.Intents.all()
intents.message_content = True

load_dotenv('.env')
token = os.getenv("TOKEN")

bot = commands.Bot(
    command_prefix="?",
    case_insensitive=True,
    intents=intents
)

@bot.event
async def on_ready():
    print("Cleared to take off!")

@bot.command()
async def dice(ctx, m: int, n: int): # mDnを実行
    if ctx.author.bot:
        return

    if m < 1:
        await ctx.reply("1回より多く振ってください")
        return
    if n < 1:
        await ctx.reply("1より大きなダイスにしてください")
        return

    total = 0
    for i in range(m):
        total += random.randint(1, n)
    await ctx.reply(total)

@bot.event
async def on_message(ctx):
    if ctx.author.bot:
        return
    await bot.process_commands(ctx)

    # メッセージが「int+"d"+int」の形式に一致するかチェック
    pattern = r'^(\d+)d(\d+)$'
    match = re.match(pattern, ctx.content)

    if match:
        rolls = int(match.group(1))
        sides = int(match.group(2))

        if rolls < 1 or sides < 1:
            await ctx.reply("Specify the number of dice and the number of sides to be 1 or more.")
            return

        result = roll_dice(rolls,sides)

        await ctx.reply(f"{rolls}d{sides} -> {result}")
    

    # メッセージに「{{int+"d"+int}}」の形式が含まれているかチェック
    pattern = r'\{\{(\d+)d(\d+)\}\}'
    matches = re.finditer(pattern, ctx.content)

    new_message_parts = []
    last_end = 0

    for match in matches:
        rolls = int(match.group(1))
        sides = int(match.group(2))

        if rolls < 1 or sides < 1:
            await ctx.reply("Specify the number of dice and the number of sides to be 1 or more.")
            return

        result = roll_dice(rolls,sides)

        # 変更後のメッセージ
        new_message_parts.append(ctx.content[last_end:match.start()])
        new_message_parts.append(str(result))
        last_end = match.end()

    new_message_parts.append(ctx.content[last_end:])

    new_message = ''.join(new_message_parts)

    # 変更がある場合のみ返信
    if new_message != ctx.content:
        await ctx.reply(new_message)

def roll_dice(rolls:int,sides:int):
    result:int
    result = 0
    for i in range(rolls):
        result += random.randint(1, sides)
    return result

# ボットの実行
bot.run(token)