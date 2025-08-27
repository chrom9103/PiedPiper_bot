import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import re

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
    print(f"Logged in as {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)

    pattern = r'^((にゃ|にゃー)\s*)+$'
    match = re.match(pattern, message.content)

    if match:
        morse_code = message.content.replace('にゃー', '-').replace('にゃ', '.')
        print(morse_code)

        morse_dict = {
            # アルファベット
            '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E',
            '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J',
            '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O',
            '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T',
            '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y',
            '--..': 'Z',
            # 数字
            '-----': '0', '.----': '1', '..---': '2', '...--': '3',
            '....-': '4', '.....': '5', '-....': '6', '--...': '7',
            '---..': '8', '----.': '9',
            # 記号
            '.-.-.-': '.', '--..--': ',', '..--..': '?', '-..-.': '/',
            '-....-': '-', '.----.': "'", '-...-': '=', '.-..-.': '"',
            '.--.-.': '@', '---...': ':', '-.-.-.': ';', '...-..-': '$',
            '.-...': '&',
        }

        morse_letters = morse_code.split()
        result = ''
        for letter in morse_letters:
            result += morse_dict.get(letter, '?')
        await message.reply(f"{result}")

@bot.command()
async def ping(ctx):
    if ctx.author.bot:
        return
    file = os.path.basename(__file__)
    await ctx.reply(f"pong [{file}]")

bot.run(token)