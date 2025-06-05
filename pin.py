import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import re

load_dotenv('.env')
token = os.getenv("TOKEN")
if not token:
    raise ValueError("Discordトークンが設定されていません。")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="?", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.tree.command(name="pin", description="Pin a message in the channel")
@app_commands.describe(message="The message to pin")
async def pin(interaction: discord.Interaction, message: str):
    if interaction.user.bot:
        return

    # メッセージURLからチャンネルIDとメッセージIDを抽出
    url_pattern = r"https://discord\.com/channels/\d+/(\d+)/(\d+)"
    match = re.match(url_pattern, message)
    if not match:
        await interaction.response.send_message(
            "有効なDiscordメッセージURLを入力してください。",
            ephemeral=True
        )
        return

    channel_id = int(match.group(1))
    message_id = int(match.group(2))

    try:
        channel = await bot.fetch_channel(channel_id)
    except discord.NotFound:
        await interaction.response.send_message(
            "チャンネルが見つかりません。",
            ephemeral=True
        )
        return

    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message(
            "指定されたチャンネルはテキストチャンネルではありません。",
            ephemeral=True
        )
        return

    try:
        msg = await channel.fetch_message(message_id)
        await msg.pin()
        await interaction.response.send_message("メッセージをピン止めしました。")
    except discord.Forbidden:
        await interaction.response.send_message(
            "ピン止めする権限がありません。",
            ephemeral=True
        )
    except discord.NotFound:
        await interaction.response.send_message(
            "メッセージが見つかりません。",
            ephemeral=True
        )
    except discord.HTTPException as e:
        await interaction.response.send_message(
            f"ピン止めに失敗しました: {e}",
            ephemeral=True
        )

@bot.command()
async def ping(ctx):
    if ctx.author.bot:
        return
    file = os.path.basename(__file__)
    await ctx.reply(f"pong [{file}]")

bot.run(token)
