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
intents.message_content = True

bot = commands.Bot(
    command_prefix="?",
    case_insensitive=True,
    intents=intents
)

@bot.event
async def on_ready():
    print("Cleared to take off!")

@bot.command()
async def mkivt(ctx):
    if ctx.author.bot:
        return

    role_id = 1304058655502503977
    role = discord.utils.get(ctx.guild.roles, id=role_id)
    if role not in ctx.author.roles:
        await ctx.send(f"Permission issue\n{role.mention}  {ctx.author.name} is creating an invite link.")

    if ctx.channel.id != 1342861713300521051:
        await ctx.reply("You cannot use this command in this channel.")
        return

    invite = await ctx.channel.create_invite(max_uses=1, max_age=0, reason=f"By {ctx.author.name}")
    await ctx.send(f"New invite link: {invite.url}")
    await ctx.send(f"Invite ID:`{invite.id}` was created by {ctx.author.name}")

    with open("logs\log_list.txt", "a") as log_file:
        log_file.write(f"Invite ID: {invite.id}. Author: {ctx.author.name}\n")

@bot.command()
async def add(ctx, role:str, *member:discord.Member):
    if ctx.author.bot:
        return

    admin_role_id = 1304058655502503977 # admin role ID
    mentor_role_id = 1304077274278133810 # mentor role ID
    admin_role = discord.utils.get(ctx.guild.roles, id=admin_role_id)
    mentor_role = discord.utils.get(ctx.guild.roles, id=mentor_role_id)

    seminar_list = [
        1371796031318130799,  # Unity
        1371795945859186831,  # web創作
        1305402941125038154,  # 課題解決
        1305402751689162835,  # 機械学習
        1371799262534303844   # discord-bot
    ]
    target_role = discord.utils.get(ctx.guild.roles, name=role)

    if ctx.channel.id != 1342861713300521051:
        await ctx.reply("You cannot use this command in this channel.")
        return
    
    try:
        if role == "member":

            if admin_role not in ctx.author.roles:
                await ctx.reply("Permission error")
                return
            
            premember_role = discord.utils.get(ctx.guild.roles, name="pre-member")
            for user in member:
                await user.add_roles(target_role)
                await user.remove_roles(premember_role)
                print(f"Added {user.name} to {target_role.name}.")

        elif target_role and target_role.id in seminar_list:

            if admin_role not in ctx.author.roles and mentor_role not in ctx.author.roles:
                await ctx.reply("Permission error")
                return
            
            for user in member:
                await user.add_roles(target_role)
                print(f"Added {user.name} to {target_role.name}.")

    except discord.Forbidden:
        print("Permission error")
    except discord.HTTPException as e:
        print(f"An error occurred: {e}")

@bot.command()
async def ping(ctx):
    if ctx.author.bot:
        return
    file = os.path.basename(__file__)
    await ctx.reply(f"pong [{file}]")

bot.run(token)
