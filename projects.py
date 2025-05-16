import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import re

intents = discord.Intents.all()
intents.messages = True
intents.message_content = True

load_dotenv('.env')
token = os.getenv("TOKEN")

bot = commands.Bot(
    command_prefix="?",
    case_insensitive=True,
    intents=intents
)

LOG_FILE = "chat_log.txt"

@bot.event
async def on_ready():
    print("Cleared to take off!")

@bot.command()
async def newProject(ctx,name:str,*members:discord.Member):
    if ctx.author.bot:
        return
    
    guild = ctx.guild

    if not isCreateable(guild, name):
        await ctx.channel.send("Name must be unique and not a mention.")
        return

    member_list = list(members)

    if len(member_list) < 2:
        await ctx.channel.send("A project must have at least two members.")
        return
    
    role = await guild.create_role(name=name)
    for member in member_list:
        await member.add_roles(role)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        role: discord.PermissionOverwrite(view_channel=True),  # {name}ロールにアクセス権限を付与
    }

    # カテゴリを作成
    category = await guild.create_category(name, overwrites=overwrites)
    await guild.create_text_channel("雑談", category=category)
    await guild.create_text_channel("会議室", category=category)
    await guild.create_voice_channel("VC", category=category)

    target_channel = discord.utils.get(guild.channels, name="管理者")
    if target_channel:
        await category.edit(position=target_channel.position + 1, after=target_channel)
    else:
        await ctx.channel.send("The target channel was not found.")

@bot.command()
async def deleteProject(ctx,name:str):
    if ctx.author.bot:
        return

    if isProject(ctx.guild, name):
        # Guildオブジェクトの取得
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name=name)
        category = discord.utils.get(guild.categories, name=name)

        try:

            #Project用ロールを削除
            await role.delete()
            #権限設定を変更
            role = discord.utils.get(guild.roles, name="member")
            overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=False,
                send_messages_in_threads=False,
                create_public_threads=False,
                connect=False)
            }
            for channel in category.channels:
                await channel.edit(overwrites=overwrites, sync_permissions=True) #カテゴリと同期
            #カテゴリ名をお蔵入りに
            await category.edit(name="【お蔵】" + name, overwrites=overwrites)
            all_categories = guild.categories
            highest_position = max([category.position for category in all_categories], default=0)
            await category.edit(position=highest_position + 1)
            
            await ctx.channel.send(f"Project：{name} was completed.")

        except discord.Forbidden:
            await ctx.send("The bot does not have permission to edit this channel.")
        except discord.HTTPException as e:
            await ctx.send(f"An error has occurred: {e}")
    else:
        await ctx.channel.send(f"{name} was not been found.")

@bot.command()
async def addProject(ctx,category_name:str,ch_type: str,ch_name:str):
    if ctx.author.bot:
        return

    guild = ctx.guild

    category = discord.utils.get(guild.categories, name=category_name)

    if category is None:
        await ctx.send(f"category'{category_name}' was not been found.")
        return

    if not isProject(guild, category_name):
        await ctx.send(f"Category '{category_name}' is not a valid project.")
        return

    if ch_type == "text-ch":
        await guild.create_text_channel(ch_name, category=category)  # 正しいカテゴリを指定
        await ctx.send(f"Added text channel '{ch_name}' to category '{category_name}'.")
    elif ch_type == "voice-ch":
        await guild.create_voice_channel(ch_name, category=category)  # 正しいカテゴリを指定
        await ctx.send(f"Added voice channel '{ch_name}' to category '{category_name}'.")
    else:
        await ctx.send("ch_type must be 'text-ch' or 'voice-ch'.")

@bot.command()
async def rename(ctx,ch_type:str,old_name:str,new_name:str):
    if ctx.author.bot:
        return

    guild = ctx.guild

    if ch_type == "text-ch":
        channel = discord.utils.get(guild.text_channels, name=old_name)
    elif ch_type == "voice-ch":
        channel = discord.utils.get(guild.voice_channels, name=old_name)
    else:
        await ctx.send("ch_type must be 'text-ch' or 'voice-ch'.")
        return

    if channel is None:
        await ctx.send(f"channel '{old_name}' was not found.")
        return

    try:
        # チャンネルの名前を変更
        await channel.edit(name=new_name)
        await ctx.send(f"'{old_name}' has been changed to '{new_name}'.")
    except discord.Forbidden:
        await ctx.send("The bot does not have permission to edit this channel.")
    except discord.HTTPException as e:
        await ctx.send(f"An error has occurred: {e}")

@bot.command()
async def setVCstatus(ctx,name:str):
    if ctx.author.bot:
        return

    if ctx.author.voice and ctx.author.voice.channel:
        voice_channel = ctx.author.voice.channel
    else:
        await ctx.send("You are not in a voice channel")
        return
    
    try:
        await voice_channel.edit(status=name)
    except discord.Forbidden:
        await ctx.send("The bot does not have permission to edit this channel.")
    except discord.HTTPException as e:
        await ctx.send(f"An error has occurred: {e}")

def isProject(guild:discord.Guild, name:str):
    role = discord.utils.get(guild.roles, name=name)
    category = discord.utils.get(guild.categories, name=name)

    if role is None or category is None or role.color != discord.Color.default():
        print("role ot category not mutch")
        return False

    overwrites = category.overwrites
    if role in overwrites and any(value is not None for value in overwrites[role]):
        print("overwrites is set")
        return True

    return False

def isCreateable(guild:discord.Guild, name:str):

    pattern = r'^<@(\d+)$'
    match = re.match(pattern, name)
    if match:
        return False
    
    for category in guild.categories:
        if category.name == name:
            return False
    
    return True

@bot.command()
async def export(ctx, limit: int = 100):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("管理者権限が必要です。")
        return

    messages = []
    async for message in ctx.channel.history(limit=limit):
        messages.append(f"[{message.created_at}] {message.author}: {message.content}:{message.attachments}")

    # メッセージをファイルに保存
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(messages))

    await ctx.send(f"{limit} 件のメッセージを {LOG_FILE} にエクスポートしました。")

@bot.command()
async def ping(ctx):
    if ctx.author.bot:
        return
    file = os.path.basename(__file__)
    await ctx.reply(f"pong [{file}]")

bot.run(token)
