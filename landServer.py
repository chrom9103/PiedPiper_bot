import os
import discord
from discord.ext import commands
from discord import Permissions
from dotenv import load_dotenv
import datetime
import schedule
import asyncio

load_dotenv('.env')
token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="?",
    case_insensitive=True,
    intents=intents
)

@bot.event
async def on_ready():
    print("Cleard to take off!")
    schedule.every().day.at("00:00").do(asyncio.create_task, job())

    async def schedule_runner():
        while True:
            schedule.run_pending()
            await asyncio.sleep(0.01)# 非同期で0.1秒間隔でチェック

    bot.loop.create_task(schedule_runner())

async def job():
    print(datetime.datetime.now())
    print("I'm working...")

    guild_id = 1327102300690448385  # 対象サーバーID
    role_names = ["member", "pre_member"]  # 権限を変更するロール名リスト

    guild = bot.get_guild(guild_id)
    if guild:
        for role_name in role_names:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                current_permissions = role.permissions
                permissions = Permissions(
                    send_messages=False,
                    send_messages_in_threads=False,
                    create_public_threads=False,
                    connect=False
                )
                await role.edit(permissions=permissions)

                print(f"Permissions for '{role_name}' have been updated.")
            else:
                print(f"Role '{role_name}' not found.")
    else:
        print(f"Guild with ID '{guild_id}' not found.")
    
    guild_id =1327101890403504238   # 対象サーバーID（適切なIDに置き換えてください）
    role_names = ["pre-member", "member"]  # 権限を変更するロール名リスト

    guild = bot.get_guild(guild_id)
    if guild:
        for role_name in role_names:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                current_permissions = role.permissions
                permissions = Permissions(
                    send_messages=True,
                    send_messages_in_threads=True,
                    create_public_threads=True
                )
                permissions.value |= current_permissions.value

                await role.edit(permissions=permissions)

                print(f"Permissions for '{role_name}' have been updated.")
            else:
                print(f"Role '{role_name}' not found.")
    else:
        print(f"Guild with ID '{guild_id}' not found.")

bot.run(token)
