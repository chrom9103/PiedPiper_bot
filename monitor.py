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

@bot.event
async def on_message_edit(before, after):
    channel = bot.get_channel(notification_channel_id)
    if channel:
        try:
            notify_member = await bot.fetch_user(before.author.id)
            before_content = before.content if before.content else "*No text content*"
            after_content = after.content if after.content else "*No text content*"
            
            embed = discord.Embed(
                description=f"{notify_member} updated a message in [{before.channel.mention}]",
                color=0xff0000
            )
            embed.add_field(name="Now", value=after_content, inline=False)
            embed.add_field(name="Previous", value=before_content, inline=False)

            await channel.send(embed=embed)
        except discord.DiscordException as e:
            print(f"Error sending message: {e}")


@bot.event
async def on_message_delete(message):
    channel = bot.get_channel(notification_channel_id)

    if channel:
        try:
            notify_member = await bot.fetch_user(message.author.id)
            content = message.content if message.content else "*No text content*"

            embed = discord.Embed(
                description=f"{notify_member} deleted a message in {message.channel.mention}",
                color=0xff0000
            )
            embed.add_field(name="Content", value=content, inline=False)

            await channel.send(embed=embed)
        except discord.DiscordException as e:
            print(f"Error sending message: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    channel = bot.get_channel(notification_channel_id)

    if before.channel is None and after.channel is not None:
        if channel:
            embed = discord.Embed(
                description=f"{member.name} joined voice channel [{after.channel.name}] .",
                color=0xff0000
            )
            
    if after.channel is None and before.channel is not None:
        if channel:
            embed = discord.Embed(
                description=f"{member.name} left voice channel [{before.channel.name}] .",
                color=0xff0000
            )

    try:
        await channel.send(embed=embed)
    except discord.DiscordException as e:
        print(f"Error sending message: {e}")

@bot.command()
async def ping(ctx):
    if ctx.author.bot:
        return
    file = os.path.basename(__file__)
    await ctx.reply(f"pong [{file}]")

bot.run(token)