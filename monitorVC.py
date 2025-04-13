import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import asyncio

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

@bot.event
async def on_voice_state_update(member, before, after):
    # when joined a voice channel
    if before.channel is None and after.channel is not None:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("db.txt", "a") as file:
                file.write(f"[{member},{current_time},0]\n")

    # when left a voice channel
    if before.channel is not None and after.channel is None:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("db.txt", "a") as file:
                file.write(f"[{member},{current_time},1]\n")

@bot.command()
async def ping(ctx):
    if ctx.author.bot:
        return
    file = os.path.basename(__file__)
    await ctx.reply(f"pong [{file}]")

bot.run(token)