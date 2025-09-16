import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import re

class ProjectManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_creatable(self, guild: discord.Guild, name: str):
        """プロジェクト名が有効かチェックします。"""
        # メンション形式ではないかチェック
        if re.match(r'^<@(\d+)>$', name):
            return False
        # 同じ名前のカテゴリが存在しないかチェック
        for category in guild.categories:
            if category.name == name:
                return False
        return True

    def is_project(self, guild: discord.Guild, name: str):
        """指定された名前のカテゴリとロールが有効なプロジェクトかチェックします。"""
        role = discord.utils.get(guild.roles, name=name)
        category = discord.utils.get(guild.categories, name=name)
        
        # ロールとカテゴリが両方存在し、色がデフォルトであることを確認
        if not role or not category or role.color != discord.Color.default():
            return False
        
        # カテゴリのオーバーライトにロールのアクセス権限が設定されているか確認
        overwrites = category.overwrites
        if role in overwrites and overwrites[role].view_channel:
            return True
            
        return False
    
    @commands.command()
    async def newProject(self, ctx, name: str, *members: discord.Member):
        if ctx.author.bot:
            return
        
        guild = ctx.guild

        if not self.is_creatable(guild, name):
            await ctx.send("プロジェクト名はユニークであり、メンション形式であってはいけません。")
            return

        member_list = list(members)
        if len(member_list) < 2:
            await ctx.send("プロジェクトには少なくとも2人のメンバーが必要です。")
            return

        try:
            role = await guild.create_role(name=name)
            for member in member_list:
                await member.add_roles(role)
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                role: discord.PermissionOverwrite(view_channel=True),
            }

            category = await guild.create_category(name, overwrites=overwrites)
            await guild.create_text_channel("雑談", category=category)
            await guild.create_text_channel("会議室", category=category)
            await guild.create_voice_channel("VC", category=category)
            
            # カテゴリの位置を調整
            target_channel = discord.utils.get(guild.channels, name="管理者")
            if target_channel:
                await category.edit(position=target_channel.position + 1)
            else:
                await ctx.send("プロジェクトカテゴリを配置する基準チャンネルが見つかりませんでした。")

            await ctx.send(f"プロジェクト `{name}` が作成されました。メンバーに `{role.mention}` ロールを付与しました。")
        except discord.Forbidden:
            await ctx.send("ボットにプロジェクトを作成する権限がありません。")
        except discord.HTTPException as e:
            await ctx.send(f"エラーが発生しました: {e}")

    @commands.command()
    async def deleteProject(self, ctx, name: str):
        if ctx.author.bot:
            return

        if not self.is_project(ctx.guild, name):
            await ctx.send(f"'{name}' という有効なプロジェクトは見つかりませんでした。")
            return

        guild = ctx.guild
        role = discord.utils.get(guild.roles, name=name)
        category = discord.utils.get(guild.categories, name=name)

        try:
            # プロジェクト用ロールを削除
            await role.delete()
            
            # 権限を編集してチャンネルをお蔵入りにする
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
            }
            
            for channel in category.channels:
                await channel.edit(overwrites=overwrites)
            
            await category.edit(name=f"【お蔵】{name}", overwrites=overwrites)
            
            # カテゴリを一番下に移動
            all_categories = sorted(guild.categories, key=lambda c: c.position)
            await category.edit(position=len(all_categories) - 1)
            
            await ctx.send(f"プロジェクト `{name}` が完了としてマークされました。")
        except discord.Forbidden:
            await ctx.send("ボットにプロジェクトを削除する権限がありません。")
        except discord.HTTPException as e:
            await ctx.send(f"エラーが発生しました: {e}")
    
    @commands.command()
    async def addProject(self, ctx, category_name: str, ch_type: str, ch_name: str):
        if ctx.author.bot:
            return
        
        guild = ctx.guild
        category = discord.utils.get(guild.categories, name=category_name)
        
        if category is None or not self.is_project(guild, category_name):
            await ctx.send(f"カテゴリ '{category_name}' は有効なプロジェクトではありません。")
            return

        try:
            if ch_type.lower() == "text-ch":
                await guild.create_text_channel(ch_name, category=category)
                await ctx.send(f"テキストチャンネル `{ch_name}` をカテゴリ `{category_name}` に追加しました。")
            elif ch_type.lower() == "voice-ch":
                await guild.create_voice_channel(ch_name, category=category)
                await ctx.send(f"ボイスチャンネル `{ch_name}` をカテゴリ `{category_name}` に追加しました。")
            else:
                await ctx.send("`ch_type`は`text-ch`または`voice-ch`である必要があります。")
        except discord.Forbidden:
            await ctx.send("ボットにチャンネルを作成する権限がありません。")
        except discord.HTTPException as e:
            await ctx.send(f"エラーが発生しました: {e}")

    @commands.command()
    async def rename(self, ctx, ch_type: str, old_name: str, new_name: str):
        if ctx.author.bot:
            return

        guild = ctx.guild
        channel = None
        
        if ch_type.lower() == "text-ch":
            channel = discord.utils.get(guild.text_channels, name=old_name)
        elif ch_type.lower() == "voice-ch":
            channel = discord.utils.get(guild.voice_channels, name=old_name)
        else:
            await ctx.send("`ch_type`は`text-ch`または`voice-ch`である必要があります。")
            return

        if channel is None:
            await ctx.send(f"チャンネル`{old_name}`は見つかりませんでした。")
            return

        try:
            await channel.edit(name=new_name)
            await ctx.send(f"`{old_name}`を`{new_name}`に変更しました。")
        except discord.Forbidden:
            await ctx.send("ボットにチャンネル名を変更する権限がありません。")
        except discord.HTTPException as e:
            await ctx.send(f"エラーが発生しました: {e}")

    @commands.command()
    async def setVCstatus(self, ctx, name: str):
        if ctx.author.bot:
            return

        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("ボイスチャンネルに接続していません。")
            return
        
        voice_channel = ctx.author.voice.channel
        
        try:
            # チャンネルのトピックをステータスとして設定する
            await voice_channel.edit(topic=name)
            await ctx.send(f"ボイスチャンネルのトピックを`{name}`に設定しました。")
        except discord.Forbidden:
            await ctx.send("ボットにチャンネルを編集する権限がありません。")
        except discord.HTTPException as e:
            await ctx.send(f"エラーが発生しました: {e}")
    
    @commands.command()
    async def export(self, ctx, limit: int = 100):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("管理者権限が必要です。")
            return
        
        try:
            messages = []
            async for message in ctx.channel.history(limit=limit, oldest_first=True):
                attachments_info = ", ".join([att.url for att in message.attachments])
                messages.append(f"[{message.created_at}] {message.author}: {message.content} - Attachments: [{attachments_info}]")

            # ログディレクトリが存在しない場合は作成
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("\n".join(messages))

            await ctx.send(f"✅ {limit} 件のメッセージを`{self.log_file}`にエクスポートしました。")
        except discord.Forbidden:
            await ctx.send("メッセージ履歴を読み取る権限がありません。")
        except discord.HTTPException as e:
            await ctx.send(f"エクスポート中にエラーが発生しました: {e}")


async def setup(bot):
    await bot.add_cog(ProjectManagerCog(bot))