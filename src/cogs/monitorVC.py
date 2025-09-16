import discord
from discord.ext import commands
import os
from datetime import datetime

class VoiceLoggerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_dir = "logs"
        
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """ボイスチャンネルの入退室をログに記録します。"""
        # ログファイルパスを動的に生成
        log_file_path = os.path.join(self.log_dir, f"vc_log_{datetime.now().strftime('%Y-%m')}.txt")

        # 参加時
        if before.channel is None and after.channel is not None:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file_path, "a") as file:
                file.write(f"{member},{current_time},0\n")

        # 退出時
        if before.channel is not None and after.channel is None:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file_path, "a") as file:
                file.write(f"{member},{current_time},1\n")

async def setup(bot):
    await bot.add_cog(VoiceLoggerCog(bot))