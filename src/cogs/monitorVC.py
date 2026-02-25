import discord
from discord.ext import commands
from datetime import datetime, timezone
from utils.database import db


class VoiceLoggerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """ボイスチャンネルの入退室をDBに記録する"""
        now = datetime.now(timezone.utc)

        # 参加時
        if before.channel is None and after.channel is not None:
            # ユーザー情報を更新
            await db.upsert_user(
                user_id=member.id,
                username=member.name,
                display_name=member.display_name,
            )
            # セッション開始
            await db.open_session(
                user_id=member.id,
                guild_id=after.channel.guild.id,
                channel_id=after.channel.id,
                join_time=now,
            )

        # 退出時
        elif before.channel is not None and after.channel is None:
            await db.close_session(
                user_id=member.id,
                guild_id=before.channel.guild.id,
                left_time=now,
            )


async def setup(bot):
    await bot.add_cog(VoiceLoggerCog(bot))