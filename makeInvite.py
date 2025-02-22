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
intents.messages = True

bot = commands.Bot(
    command_prefix="?",
    case_insensitive=True,
    intents=intents
)

# 設定
notification_channel_id = 1327101891628503152  # 通知を送信するチャンネルのID

@bot.event
async def on_ready():
    print("Cleared to take off!")

@bot.command()
async def mkivt(ctx):
    if ctx.author.bot:
        role_id = 1304058655502503977
        role = discord.utils.get(ctx.guild.roles, id=role_id)
        print(role)
        if role not in ctx.author.roles:
            await ctx.reply("Permission error")
            if ctx.channel.id != 1342861713300521051:
                await ctx.reply("You cannot use this command in this channel.")
                return
        
        print("Creating invite link...")

    invite = await ctx.channel.create_invite(max_uses=1, max_age=0, reason=f"By {ctx.name}", target_user=ctx.author )
    await ctx.reply(f"New invite link: {invite.url}")


@bot.command()
async def ping(ctx):
    if ctx.author.bot:
        return
    file = os.path.basename(__file__)
    await ctx.reply(f"pong [{file}]")

bot.run(token)