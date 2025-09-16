import discord
from discord.ext import commands
import random
import re

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
        label_part = f"【{label}】 " if label else ""

        return f"{label_part}({base}<={limit}) > {result} > {msg}"
    else:
        return f"{base} -> {result}"

# コグクラス
class DiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 従来の`on_message`機能をコマンドとして再実装
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        content = message.content.strip()

        # 1. "{{XdY}}"
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
            rolls, sides, limit = int(rolls), int(sides), int(limit)
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
        
        # 4. "XdY 【LABEL】"
        pattern_labeled_simple = r'^(\d+)[dD](\d+)\s*【\s*(.+?)\s*】$'
        match = re.match(pattern_labeled_simple, content)
        if match:
            rolls, sides, label = map(str.strip, match.groups())
            rolls, sides = int(rolls), int(sides)
            if rolls >= 1 and sides >= 1:
                response = create_dice_response(rolls, sides, label=label)
                await message.reply(response)
            return

        # 5. "XdY"
        pattern_simple = r'^(\d+)[dD](\d+)$'
        match = re.match(pattern_simple, content)
        if match:
            rolls, sides = map(int, match.groups())
            if rolls >= 1 and sides >= 1:
                response = create_dice_response(rolls, sides)
                await message.reply(response)
            return
        
        await self.bot.process_commands(message)


async def setup(bot):
    await bot.add_cog(DiceCog(bot))