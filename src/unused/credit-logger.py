import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import re
from datetime import datetime

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
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# @bot.tree.command(name="pin", description="Pin a message in the channel")
# @app_commands.describe(message_url="The message to pin")
# async def record(interaction: discord.Interaction, mode: str):
#     if interaction.user.bot:
#         return

@bot.event
async def on_voice_state_update(member, before, after):
    # when joined a voice channel
    if before.channel is None and after.channel is not None:
            os.makedirs("datas", exist_ok=True)
            with open(f"datas/on_vc.txt", "a") as file:
                file.write(f"{member}\n")

    # when left a voice channel
    if before.channel is not None and after.channel is None:
            os.makedirs("datas", exist_ok=True)
            file = open(f"datas/on_vc.txt", "a")
            with open("datas/on_vc.txt", "r") as file:
                lines = file.readlines()

            updated_lines = []
            for line in lines:
                if member.display_name not in line:
                    updated_lines.append(line)

@bot.command()
async def ping(ctx):
    if ctx.author.bot:
        return
    file = os.path.basename(__file__)
    await ctx.reply(f"pong [{file}]")

bot.run(token)
