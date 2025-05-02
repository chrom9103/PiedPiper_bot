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

    with open("log_list.txt", "a") as log_file:
        log_file.write(f"Invite ID: {invite.id}. Author: {ctx.author.name}\n")

@bot.command()
async def add(ctx, mode:str, *member:discord.Member):
    if ctx.author.bot:
        return

    role_id = 1304058655502503977
    role = discord.utils.get(ctx.guild.roles, id=role_id)

    if role not in ctx.author.roles:
        await ctx.reply("Permission error")
        return

    if ctx.channel.id != 1342861713300521051:
        await ctx.reply("You cannot use this command in this channel.")
        return
    
    try:
        if mode == "member":
            member_role = discord.utils.get(ctx.guild.roles, name="member")
            premember_role = discord.utils.get(ctx.guild.roles, name="pre-member")
            for user in member:
                await user.add_roles(member_role)
                await user.remove_roles(premember_role)
                print(f"Added {user.name} to {member_role.name}.")
                with open("addList.txt", "a") as file:
                    file.write(f"{member}\n")
    except discord.Forbidden:
        await print("Permission error")
    except discord.HTTPException as e:
        await print(f"An error occurred: {e}")

@bot.command()
async def ping(ctx):
    if ctx.author.bot:
        return
    file = os.path.basename(__file__)
    await ctx.reply(f"pong [{file}]")

bot.run(token)
