import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import random
import re

load_dotenv('.env')
token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN is not set in the .env file.")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", case_insensitive=True, intents=intents)

# ダイスを振る関数
def roll_dice(rolls: int, sides: int) -> int:
    return sum(random.randint(1, sides) for _ in range(rolls))

# ダイス結果をメッセージとして生成
def create_dice_response(rolls: int, sides: int, limit: int = None, label: str = None):
    result = roll_dice(rolls, sides)
    base = f"{rolls}d{sides}"

    if limit is not None:
        # 成功等のメッセージを生成
        msg = ""
        if result <= limit:
            msg = "成功"
            if rolls == 1 and sides == 100:
                if result <= 5:
                    msg = "決定的成功/スペシャル"
        else:
            msg = "失敗"
            if rolls == 1 and sides == 100:
                if result >= 96:
                    msg = "致命的失敗"
        
        # 【LABEL】がある場合はそれを追加
        if label:
            label_part = f"【{label}】 "
        else:
            label_part = ""

        return f"{label_part}({base}<={limit}) > {result} > {msg}"
    else:
        return f"{base} -> {result}"

@bot.event
async def on_ready():
    print("Cleared to take off!")

@bot.command()
async def dice(ctx, m: int, n: int):
    if ctx.author.bot:
        return
    if m < 1:
        await ctx.reply("1回より多く振ってください")
        return
    if n < 1:
        await ctx.reply("1より大きなダイスにしてください")
        return
    total = roll_dice(m, n)
    await ctx.reply(total)

@bot.command()
async def ping(ctx):
    if ctx.author.bot:
        return
    file = os.path.basename(__file__)
    await ctx.reply(f"pong [{file}]")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

    content = message.content.strip()

    # 1. "{{XdY}}" を置換
    inline_pattern = r'\{\{(\d+)[dD](\d+)\}\}'
    modified = False

    def replace_inline(match):
        nonlocal modified
        rolls = int(match.group(1))
        sides = int(match.group(2))
        if rolls < 1 or sides < 1:
            return match.group(0)
        modified = True
        return str(roll_dice(rolls, sides))

    new_content = re.sub(inline_pattern, replace_inline, content)
    if modified:
        await message.reply(new_content)
        return

    # 2. "XdY<=Z 【LABEL】"
    pattern_labeled = r'^(\d+)[dD](\d+)\s*<=\s*(\d+)\s*【\s*(.+?)\s*】$'
    match = re.match(pattern_labeled, content)
    if match:
        rolls, sides, limit, label = map(str.strip, match.groups())
        rolls = int(rolls)
        sides = int(sides)
        limit = int(limit)
        if rolls >= 1 and sides >= 1:
            response = create_dice_response(rolls, sides, limit, label)
            await message.reply(response)
        return

    # 3. "XdY<=Z"
    pattern_limit = r'^(\d+)[dD](\d+)\s*<=\s*(\d+)$'
    match = re.match(pattern_limit, content)
    if match:
        rolls, sides, limit = map(int, match.groups())
        if rolls >= 1 and sides >= 1:
            response = create_dice_response(rolls, sides, limit)
            await message.reply(response)
        return

    # 4. "XdY"
    pattern_simple = r'^(\d+)[dD](\d+)$'
    match = re.match(pattern_simple, content)
    if match:
        rolls, sides = map(int, match.groups())
        if rolls >= 1 and sides >= 1:
            response = create_dice_response(rolls, sides)
            await message.reply(response)
        return

bot.run(token)
