import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv('.env')
token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="?",
    case_insensitive=True,
    intents=intents
)

# サーバー名とIDの辞書
guilds_info = {
    "main": 1304058364560543815,
    "expt": 1372020363831017626
}

@bot.event
async def on_ready():
    for guild_name, guild_id in guilds_info.items():
        guild = bot.get_guild(guild_id)
        if guild is None:
            print(f"Guild '{guild_name}' not found.")
            continue

        lines = []
        for role in reversed(guild.roles):
            if role.is_default():
                continue  # @everyoneは除外
            lines.append(f"{role.name} = {role.id}")

        file_path = f"./datas/{guild_name}_roleID.env"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"Role IDs for '{guild_name}' have been saved to {file_path}.")

bot.run(token)