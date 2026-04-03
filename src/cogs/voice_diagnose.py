"""
on_voice_state_updateイベントのすべての発火パターンを記録するスクリプト

monitorVC.py に before/after の全パターンをログしてイベント発火を把握する
"""

import discord
from discord.ext import commands
from datetime import datetime, timezone
from pathlib import Path
import json


class VoiceEventDiagnosisCog(commands.Cog):
    """すべてのボイスイベントをログして診断"""

    def __init__(self, bot):
        self.bot = bot
        self.log_file = Path('./logs/voice_events.log')
        self.event_count = {
            'total': 0,
            'join': 0,  # None -> Channel (vcへの参加)
            'leave': 0,  # Channel -> None (vcから退出)
            'move': 0,  # Channel -> Channel (vc移動)
            'state_change': 0,  # その他の状態変化 (ミュートなど)
        }

    def _log_event(self, event_type: str, member: discord.Member, before, after):
        """イベントをログファイルに記録"""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        before_channel = f"{before.channel.id}({before.channel.name})" if before.channel else "None"
        after_channel = f"{after.channel.id}({after.channel.name})" if after.channel else "None"
        
        log_entry = {
            'timestamp': timestamp,
            'event_type': event_type,
            'user_id': member.id,
            'username': member.name,
            'display_name': member.display_name,
            'before_channel': before_channel,
            'after_channel': after_channel,
            'before_mute': before.self_mute,
            'after_mute': after.self_mute,
            'before_deaf': before.self_deaf,
            'after_deaf': after.self_deaf,
            'before_video': before.self_video,
            'after_video': after.self_video,
        }
        
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """全ボイスイベントを監視"""
        self.event_count['total'] += 1
        
        before_channel = before.channel
        after_channel = after.channel

        # パターン判定
        if before_channel is None and after_channel is not None:
            # VC参加
            self.event_count['join'] += 1
            self._log_event('JOIN', member, before, after)
            print(f"[{self.event_count['total']:04d}] JOIN: {member.display_name or member.name} -> #{after_channel.name}")

        elif before_channel is not None and after_channel is None:
            # VC退出
            self.event_count['leave'] += 1
            self._log_event('LEAVE', member, before, after)
            print(f"[{self.event_count['total']:04d}] LEAVE: {member.display_name or member.name} <- #{before_channel.name}")

        elif before_channel is not None and after_channel is not None and before_channel != after_channel:
            # VC移動
            self.event_count['move'] += 1
            self._log_event('MOVE', member, before, after)
            print(f"[{self.event_count['total']:04d}] MOVE: {member.display_name or member.name} #{before_channel.name} -> #{after_channel.name}")

        else:
            # その他の状態変化（ミュート、デフ、ビデオなど）
            self.event_count['state_change'] += 1
            self._log_event('STATE_CHANGE', member, before, after)
            print(f"[{self.event_count['total']:04d}] STATE: {member.display_name or member.name} (mute: {after.self_mute}, deaf: {after.self_deaf}, video: {after.self_video})")

        # 定期的に統計を出力
        if self.event_count['total'] % 10 == 0:
            print(f"\n📊 イベント統計 (合計: {self.event_count['total']})")
            print(f"   JOIN: {self.event_count['join']}")
            print(f"   LEAVE: {self.event_count['leave']}")
            print(f"   MOVE: {self.event_count['move']}")
            print(f"   STATE_CHANGE: {self.event_count['state_change']}\n")


async def setup(bot):
    await bot.add_cog(VoiceEventDiagnosisCog(bot))
