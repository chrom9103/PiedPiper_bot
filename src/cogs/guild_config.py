import discord
from discord.ext import commands
import os

class ManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_dir = "logs"
        self.log_file_path = os.path.join(self.log_dir, "log_list.txt")

        # ログディレクトリが存在しない場合は作成
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    @commands.command()
    async def mkivt(self, ctx):
        if ctx.author.bot:
            return

        # ロールIDとチャンネルIDを定数として定義
        required_role_id = 1304058655502503977
        required_channel_id = 1342861713300521051
        
        required_role = discord.utils.get(ctx.guild.roles, id=required_role_id)
        
        # 権限とチャンネルのチェック
        if required_role not in ctx.author.roles:
            await ctx.send(f"Permission issue\n{required_role.mention} {ctx.author.name} is creating an invite link.")
            return

        if ctx.channel.id != required_channel_id:
            await ctx.reply("このチャンネルではコマンドを使用できません。")
            return

        try:
            invite = await ctx.channel.create_invite(max_uses=1, max_age=0, reason=f"By {ctx.author.name}")
            await ctx.send(f"New invite link: {invite.url}")
            await ctx.send(f"Invite ID:`{invite.id}` was created by {ctx.author.name}")
            
            with open(self.log_file_path, "a") as log_file:
                log_file.write(f"Invite ID: {invite.id}. Author: {ctx.author.name}\n")
        
        except discord.Forbidden:
            await ctx.reply("招待を作成する権限がありません。")
        except discord.HTTPException as e:
            await ctx.reply(f"エラーが発生しました: {e}")

    @commands.command()
    async def add(self, ctx, role: str, *members: discord.Member):
        if ctx.author.bot:
            return

        # ロールIDを定数として定義
        admin_role_id = 1304058655502503977
        mentor_role_id = 1304077274278133810
        required_channel_id = 1342861713300521051
        
        admin_role = discord.utils.get(ctx.guild.roles, id=admin_role_id)
        mentor_role = discord.utils.get(ctx.guild.roles, id=mentor_role_id)
        
        # 権限チェックのための関数
        def has_permission():
            return admin_role in ctx.author.roles or mentor_role in ctx.author.roles

        seminar_list = [
            1371796031318130799,  # Unity
            1371795945859186831,  # web創作
            1305402941125038154,  # 課題解決
            1305402751689162835,  # 機械学習
            1371799262534303844  # discord-bot
        ]

        target_role = discord.utils.get(ctx.guild.roles, name=role)

        if ctx.channel.id != required_channel_id:
            await ctx.reply("このチャンネルではコマンドを使用できません。")
            return
        
        try:
            # "member"ロールの処理
            if role.lower() == "member":
                if admin_role not in ctx.author.roles:
                    await ctx.reply("この操作には管理者権限が必要です。")
                    return
                
                premember_role = discord.utils.get(ctx.guild.roles, name="pre-member")
                if not premember_role or not target_role:
                    await ctx.reply("必要なロールが見つかりませんでした。")
                    return
                
                for user in members:
                    await user.add_roles(target_role)
                    await user.remove_roles(premember_role)
                    print(f"Added {user.name} to {target_role.name}.")
                await ctx.reply(f"指定されたユーザーに`{target_role.name}`ロールを付与しました。")

            # セミナーロールの処理
            elif target_role and target_role.id in seminar_list:
                if not has_permission():
                    await ctx.reply("この操作には管理者またはメンター権限が必要です。")
                    return
                
                for user in members:
                    await user.add_roles(target_role)
                    print(f"Added {user.name} to {target_role.name}.")
                await ctx.reply(f"指定されたユーザーに`{target_role.name}`ロールを付与しました。")
            
            else:
                await ctx.reply("指定されたロールは付与できません。")

        except discord.Forbidden:
            await ctx.reply("必要な権限がありません。")
        except discord.HTTPException as e:
            await ctx.reply(f"エラーが発生しました: {e}")

async def setup(bot):
    await bot.add_cog(ManagementCog(bot))