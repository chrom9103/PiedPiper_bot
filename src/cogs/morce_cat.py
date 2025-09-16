import discord
from discord.ext import commands
import os
import re

class MorseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # モールス信号の辞書をクラスの属性として定義
        self.morse_dict = {
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
        # 正規表現パターンもクラスの属性として定義
        self.pattern = re.compile(r'^((にゃ|にゃー)\s*)+$')

    @commands.Cog.listener()
    async def on_message(self, message):
        """メッセージを監視し、モールス信号をデコードします。"""
        if message.author.bot:
            return
        
        # 正規表現を使ってメッセージ内容をチェック
        if self.pattern.match(message.content):
            # メッセージをモールス符号に変換
            morse_code = message.content.replace('にゃー', '-').replace('にゃ', '.').strip()
            
            morse_letters = morse_code.split()
            result = ''
            for letter in morse_letters:
                # 辞書を使ってデコードし、見つからない場合は'?'を返す
                result += self.morse_dict.get(letter, '?')
            
            await message.reply(f"{result}")
            
        # コマンドの処理を忘れずに呼び出す
        await self.bot.process_commands(message)


async def setup(bot):
    await bot.add_cog(MorseCog(bot))