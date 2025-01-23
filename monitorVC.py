import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv('.env')
token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="?",
    case_insensitive=True,
    intents=intents
)

# 設定
target_user_id = 832827630821703740  # ボイスチャットを監視するユーザーのID
notification_channel_id = 1318299905189613694  # 通知を送信するチャンネルのID
notify_member_id = 832827630821703740  # メンションするメンバーのID

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    # ボイスチャットの状態が変化したユーザーが対象のユーザーか確認
    if member.id == target_user_id:
        # ユーザーが新たにボイスチャットに参加したか確認
        if before.channel is None and after.channel is not None:
            # 通知を送信
            channel = bot.get_channel(notification_channel_id)
            notify_member = bot.get_user(notify_member_id)
            
            if channel and notify_member:
                await channel.send(f"{notify_member.mention}  {member.name} was joining {after.channel.name} に参加しました！")

@bot.command()
async def ping(ctx):
    if ctx.author.bot:
        return
    file = os.path.basename(__file__)
    await ctx.reply(f"pong [{file}]")

bot.run(token)