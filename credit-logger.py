import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import re
import datetime

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

@bot.tree.command(name="pin", description="Pin a message in the channel")
@app_commands.describe(message_url="The message to pin")
async def record(interaction: discord.Interaction, mode: str):
    if interaction.user.bot:
        return

@bot.event
async def on_voice_state_update(member, before, after):
    # when joined a voice channel
    if before.channel is None and after.channel is not None:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            os.makedirs("datas", exist_ok=True)
            with open(f"datas/on_vc.txt", "a") as file:
                file.write(f"{member}\n")

    # when left a voice channel
    if before.channel is not None and after.channel is None:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            os.makedirs("datas", exist_ok=True)
            file = open(f"datas/on_vc.txt", "a")
            datalist = file.readlines()
            for data in datalist:
                if data != member:
                    file.write(f"{member}\n")

@bot.command()
async def ping(ctx):
    if ctx.author.bot:
        return
    file = os.path.basename(__file__)
    await ctx.reply(f"pong [{file}]")

bot.run(token)
