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