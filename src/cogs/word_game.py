import discord
from discord.ext import commands
import random
import string
import time
import os
from datetime import datetime
import aiohttp
import csv
import math
import re

category: discord.CategoryChannel
log_act: discord.TextChannel
log_ch: discord.TextChannel
chat_room: discord.TextChannel
join_ch: discord.TextChannel
data = []
user_ch = {}
message_thread = []
phase_game: int
phase_game = 0
LifeConsume = {"aTrue": 1, "aFalse": -1, "b": -3, "c": -1, "d": -2, "e": 1, "f": -1}
LifeVariation = {"aTrue": -1, "aFalse": 1, "bTrue": 0, "bFalse": -2, "c": 0, "d": 0, "e": 0, "f": 0}
ranking = []
data_send = []
times = 1

def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0)."""
    if val in ('y', 'yes', 't', 'true', 'True', 'on', '1', 1):
        return True
    elif val in ('n', 'no', 'f', 'false', 'False', 'off', '0', 0):
        return False
    else:
        raise ValueError(f"invalid truth value {val!r}")

class UserData:
    """ユーザーごとのゲームデータを保持するクラス"""
    anon_user: discord.Member
    room: discord.TextChannel
    word_1: int
    word_2: str
    life: int
    has_defence: bool
    alive: int
    is_turn: bool
    has_set: bool
    display: discord.Message
    
    def __init__(self):
        self.anon_user = None
        self.room = None
        self.word_1 = None
        self.word_2 = ""
        self.life = 3
        self.has_defence = False
        self.alive = 0
        self.is_turn = False
        self.has_set = False
        self.display = None

    def data_migration(self, source_data: list, guild: discord.Guild):
        """CSVから読み込んだデータをオブジェクトに反映"""
        try:
            # ユーザーオブジェクトをIDから取得
            self.anon_user = guild.get_member(int(source_data[0]))
            if self.anon_user is None:
                # ユーザーが見つからなかった場合はNoneを保持
                print(f"User with ID {source_data[0]} not found.")
                return False
            
            # チャンネルオブジェクトを名前から取得
            self.room = discord.utils.get(guild.channels, name=source_data[1])
            if self.room is None:
                print(f"Channel with name {source_data[1]} not found.")
                return False

            self.word_1 = int(source_data[2])
            self.word_2 = str(source_data[3])
            self.life = int(source_data[4])
            self.has_defence = strtobool(source_data[5])
            self.alive = int(source_data[6])
            self.is_turn = strtobool(source_data[7])
            self.has_set = strtobool(source_data[8])
            return True
        except (ValueError, IndexError) as e:
            print(f"Data migration error: {e}")
            return False

    def output_as_list(self):
        """オブジェクトのデータをリストとして出力"""
        return [
            self.anon_user.id if self.anon_user else None,
            self.room.name if self.room else None,
            self.word_1,
            self.word_2,
            self.life,
            self.has_defence,
            self.alive,
            self.is_turn,
            self.has_set,
            self.display.id if self.display else None
        ]


def fx(x: int):
    """cコマンドの失敗確率を計算"""
    return 1 / (3 * (math.ceil(x / len(data))))


class WordGameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category: discord.CategoryChannel = None
        self.log_act: discord.TextChannel = None
        self.log_ch: discord.TextChannel = None
        self.chat_room: discord.TextChannel = None
        self.join_ch: discord.TextChannel = None
        self.data: list[UserData] = []
        self.user_ch: dict[discord.Member, discord.TextChannel] = {}
        self.message_thread: list[list[discord.Thread]] = []
        self.phase_game: int = 0
        self.life_consume = {"aTrue": 1, "aFalse": -1, "b": -3, "c": -1, "d": -2, "e": 1, "f": -1}
        self.life_variation = {"aTrue": -1, "aFalse": 1, "bTrue": 0, "bFalse": -2, "c": 0, "d": 0, "e": 0, "f": 0}
        self.ranking: list[discord.Member] = []
        self.data_send = []
        self.times = 1

    def take(self, ctx: commands.Context) -> int:
        """ctxのユーザーに対応するプレイヤー番号を取得"""
        user_id = ctx.author.id
        for i, user_data in enumerate(self.data):
            if user_data.anon_user and user_data.anon_user.id == user_id:
                return i
        return -1

    async def p(self, ctx: commands.Context) -> bool:
        """コマンドが実行可能か判断"""
        if ctx.author.bot:
            await ctx.reply("ボットはコマンドを実行できません。")
            return False
        
        player_id = self.take(ctx)
        if player_id == -1:
            await ctx.reply("ゲームに参加していません。")
            return False
        
        if self.data[player_id].alive != 0:
            await ctx.reply("あなたはすでにゲームオーバーです。")
            return False

        if not self.data[player_id].is_turn:
            await ctx.reply("あなたのターンではありません。")
            return False
        
        if self.phase_game != 2:
            await ctx.reply("ゲームのフェーズが正しくありません。")
            return False
        
        return True

    async def turn(self, now: int):
        """次のターンへ移動"""
        self.data[now].is_turn = False
        self.times += 1

        if len(self.ranking) + 1 >= len(self.data):
            await self.fin()
            return
        
        next_player_id = (now + 1) % len(self.data)
        
        # 生存者が見つかるまで次のプレイヤーを探す
        while self.data[next_player_id].alive != 0:
            next_player_id = (next_player_id + 1) % len(self.data)
        
        self.data[next_player_id].is_turn = True
        
        await self.data[next_player_id].room.send("あなたのターンです！")
        if self.data[now].alive == 0:
            await self.data[now].room.send("あなたのターンは終了しました。")
        await self.log_act.send(f"{next_player_id}'s turn!")

    async def alive(self, by: int, to: int):
        """生死判定とログの更新"""
        
        if to >= 0 and to != by and self.data[to].alive == 0:
            await self.data[to].display.edit(content=f"{to} L:{self.data[to].life} D:{self.data[to].has_defence}")

            if self.data[to].life <= 0:
                self.data[to].alive = 1
                await self.data[to].room.send("あなたは死にました！")
                await self.log_act.send(f"{to} is dead!")
                self.ranking.append(self.data[to].anon_user)
                
                # チャンネルの権限を更新（ログチャンネルの閲覧のみ許可）
                await self.log_act.set_permissions(self.data[to].anon_user, read_messages=True, send_messages=False)
                await self.log_ch.set_permissions(self.data[to].anon_user, read_messages=True, send_messages=False)
                await self.chat_room.set_permissions(self.data[to].anon_user, read_messages=True, send_messages=False)

        await self.data[by].display.edit(content=f"{by} L:{self.data[by].life} D:{self.data[by].has_defence}")
        
        if self.data[by].life <= 0:
            self.data[by].alive = 1
            await self.data[by].room.send("あなたは死にました！")
            await self.log_act.send(f"{by} is dead!")
            self.ranking.append(self.data[by].anon_user)
            
            # チャンネルの権限を更新（ログチャンネルの閲覧のみ許可）
            await self.log_act.set_permissions(self.data[by].anon_user, read_messages=True, send_messages=False)
            await self.log_ch.set_permissions(self.data[by].anon_user, read_messages=True, send_messages=False)
            await self.chat_room.set_permissions(self.data[by].anon_user, read_messages=True, send_messages=False)

    async def fin(self):
        """ゲーム終了処理"""
        for i in range(len(self.data)):
            if self.data[i].alive == 0:
                self.ranking.append(self.data[i].anon_user)

        for d in self.data:
            await d.room.send("ゲーム終了！")

        await self.chat_room.send("ゲーム終了！")
        await self.chat_room.send("ランキング発表！")
        
        for i, user in reversed(list(enumerate(self.ranking))):
            await self.chat_room.send(f"No. {i + 1}: {user.display_name}")
            
        await self.chat_room.send("お疲れ様でした！")
        await self.delete_channels()

    async def delete_channels(self):
        """チャンネルとカテゴリを削除し、ゲームをリセット"""
        # export_dataを呼び出してデータを保存
        if self.join_ch:
            await self.export_data_internal()

        for d in self.data:
            try:
                if d.room:
                    await d.room.delete()
            except Exception as e:
                print(f"Error deleting room channel: {e}")
        
        if self.log_act: await self.log_act.delete()
        if self.log_ch: await self.log_ch.delete()
        if self.chat_room: await self.chat_room.delete()
        if self.category: await self.category.delete()

        # グローバル変数をリセット
        self.category = None
        self.log_act = None
        self.log_ch = None
        self.chat_room = None
        self.data = []
        self.user_ch = {}
        self.message_thread = []
        self.phase_game = 0
        self.ranking = []
        self.data_send = []
        self.times = 1
        
        print("Channels deleted successfully.")

    async def export_data_internal(self):
        """内部でのデータエクスポート処理"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_path = f'channels_{timestamp}.csv'
        
        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([self.phase_game])
                for d in self.data:
                    d_list = d.output_as_list()
                    writer.writerow(d_list[:9])
            
            await self.join_ch.send("ゲームデータがエクスポートされました。", file=discord.File(file_path))
        except Exception as e:
            print(f"Failed to export data: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    # --- コマンド群 ---
    
    @commands.command()
    async def join(self, ctx, *member: discord.Member):
        if self.phase_game != 0:
            await ctx.reply("ゲームはすでに開始しています。")
            return
        
        members = list(member)
        if len(members) < 2:
            await ctx.reply("2人以上で参加してください。")
            return
        
        # メンバーに重複がないかチェック
        if len(members) != len(set(members)):
            await ctx.reply("同じ人が複数回指定されています。")
            return
            
        self.join_ch = ctx.channel
        self.category = await ctx.guild.create_category(name="word_game")

        overwrites_log = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False)}
        self.log_act = await self.category.create_text_channel(name="log_act", overwrites=overwrites_log)
        self.log_ch = await self.category.create_text_channel(name="log_ch", overwrites=overwrites_log)
        self.chat_room = await self.category.create_text_channel(name="chat_room")
        
        random.shuffle(members)
        word_1s = list(range(len(members)))
        random.shuffle(word_1s)

        self.data = []
        self.user_ch = {}
        self.message_thread = [[""] * len(members) for _ in range(len(members))]

        for i, member in enumerate(members):
            user_data = UserData()
            user_data.anon_user = member
            user_data.word_1 = word_1s[i]
            
            overwrites_room = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            channel = await self.category.create_text_channel(name=str(i), overwrites=overwrites_room)
            user_data.room = channel
            
            for j in range(len(members)):
                if i != j:
                    thread = await channel.create_thread(name=str(j), invitable=False)
                    self.message_thread[i][j] = thread
                    await channel.send(thread.mention)
            
            self.data.append(user_data)
            self.user_ch[member] = channel
        
        self.data[0].is_turn = True
        
        await self.log_act.send("room L D")
        for i, user_data in enumerate(self.data):
            user_data.display = await self.log_act.send(f"{i} {user_data.life} {user_data.has_defence}")
            
        await self.log_ch.send("参加メンバー:")
        for user_data in self.data:
            await self.log_ch.send(f"[{user_data.room.name}] -> {user_data.anon_user.display_name}")
            
        self.phase_game = 1
        await ctx.send("ゲーム参加者を設定しました。各チャンネルで`?set [word2]`を実行してください。")

    @commands.command()
    async def delete(self, ctx):
        if ctx.author.bot:
            return
        
        if self.phase_game == 0:
            await ctx.reply("削除するゲームがありません。")
            return
        
        await self.delete_channels()
        await ctx.send("ゲームチャンネルとカテゴリを削除し、ゲームをリセットしました。")

    @commands.command()
    async def export_data(self, ctx):
        if self.phase_game == 0:
            await ctx.reply("エクスポートするゲームがありません。")
            return
        await self.export_data_internal()

    @commands.command()
    async def import_data(self, ctx):
        if self.phase_game != 0:
            await ctx.reply("ゲームがすでに開始しています。")
            return
            
        if not ctx.message.attachments:
            await ctx.reply("CSVファイルを添付してください。")
            return
        
        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith('.csv'):
            await ctx.reply("CSVファイルのみをインポートできます。")
            return

        file_path = f'tmp_{attachment.filename}'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as response:
                    if response.status == 200:
                        with open(file_path, 'wb') as f:
                            f.write(await response.read())
            
            tmp_data = []
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                tmp_data = [row for row in reader]

            if not tmp_data or len(tmp_data) < 2:
                await ctx.reply("インポートするデータが正しくありません。")
                return

            self.phase_game = int(tmp_data[0][0])
            tmp_players_data = tmp_data[1:]
            
            self.join_ch = ctx.channel
            self.category = await ctx.guild.create_category(name="word_game_imported")
            
            overwrites_log = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False)}
            self.log_act = await self.category.create_text_channel(name="log_act", overwrites=overwrites_log)
            self.log_ch = await self.category.create_text_channel(name="log_ch", overwrites=overwrites_log)
            self.chat_room = await self.category.create_text_channel(name="chat_room")
            
            self.data = []
            self.user_ch = {}
            num_members = len(tmp_players_data)
            self.message_thread = [[""] * num_members for _ in range(num_members)]

            for i, row in enumerate(tmp_players_data):
                user_data = UserData()
                if not user_data.data_migration(row, ctx.guild):
                    await ctx.reply("データの読み込みに失敗しました。ユーザーまたはチャンネルが見つかりません。")
                    await self.delete_channels()
                    return
                
                overwrites_room = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                    user_data.anon_user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                channel = await self.category.create_text_channel(name=str(i), overwrites=overwrites_room)
                user_data.room = channel
                
                for j in range(num_members):
                    if i != j:
                        thread = await channel.create_thread(name=str(j), invitable=False)
                        self.message_thread[i][j] = thread
                        await channel.send(thread.mention)

                self.data.append(user_data)
                self.user_ch[user_data.anon_user] = channel
            
            await self.log_act.send("room L D")
            for i, user_data in enumerate(self.data):
                user_data.display = await self.log_act.send(f"{i} {user_data.life} {user_data.has_defence}")
            
            await ctx.send("ゲームデータをインポートしました。")
        except Exception as e:
            await ctx.reply(f"ファイルの処理中にエラーが発生しました: {e}")
            print(f"Import error: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    @commands.command()
    async def cheat(self, ctx, cmd: str, to: int, effect: int):
        if ctx.channel != self.chat_room:
            await ctx.reply("このコマンドは`chat_room`でのみ使用できます。")
            return
        
        if cmd == "help":
            await ctx.reply("`?cheat alive (to) (0:living, 1:dead)`\n`?cheat fixlife (to) (new life)`\n`?cheat fixdefence (to) (0:no, 1:yes)`\n`?cheat turn (next player)`")
            return

        try:
            if to < 0 or to >= len(self.data):
                await ctx.reply("無効なプレイヤーIDです。")
                return
            
            target_data = self.data[to]
            
            if cmd == "alive":
                if effect == 0:
                    target_data.alive = 0
                    target_data.life = 1
                    await ctx.send(f"プレイヤー {to} がゲームに戻りました。")
                elif effect == 1:
                    target_data.alive = 1
                    target_data.life = 0
                    await ctx.send(f"プレイヤー {to} がゲームオーバーになりました。")
                    await self.alive(self.take(ctx), to)
            elif cmd == "fixlife":
                target_data.life = effect
                await ctx.send(f"プレイヤー {to} のライフが {effect} に変更されました。")
            elif cmd == "fixdefence":
                target_data.has_defence = bool(effect)
                await ctx.send(f"プレイヤー {to} の防御ステータスが {bool(effect)} に変更されました。")
            elif cmd == "turn":
                current_player = self.take(ctx)
                if current_player == -1: return
                self.data[current_player].is_turn = False
                target_data.is_turn = True
                await ctx.send(f"次のターンはプレイヤー {to} です。")
            else:
                await ctx.reply("無効なコマンドです。`?cheat help`で確認してください。")
        except Exception as e:
            await ctx.reply(f"エラーが発生しました: {e}")

    @commands.command()
    async def set(self, ctx, *, word2: str):
        if self.phase_game != 1:
            await ctx.reply("このコマンドはゲーム開始準備フェーズでのみ使用できます。")
            return
        
        player_id = self.take(ctx)
        if player_id == -1: return
        
        self.data[player_id].word_2 = word2
        self.data[player_id].has_set = True
        
        await self.log_act.send(f"word2_player{player_id}:{word2}")
        await ctx.send(f"あなたのword1は `{self.data[player_id].word_1}`、word2は `{self.data[player_id].word_2}` です。")
        
        all_set = all(d.has_set for d in self.data)
        if all_set:
            await ctx.send("全員の準備が完了しました。ゲームを開始します。")
            self.phase_game = 2
            self.data[0].is_turn = True
            await self.data[0].room.send("あなたのターンです！")
            await self.log_act.send("0's turn!")

    @commands.command(aliases=["a"])
    async def attack(self, ctx, to: int, w1: str, *, w2: str):
        if not await self.p(ctx):
            return
        
        player_id = self.take(ctx)
        
        if to < 0 or to >= len(self.data) or self.data[to].alive != 0:
            await ctx.reply("無効なターゲットです。")
            return
        
        target_data = self.data[to]
        
        if w1 == str(target_data.word_1) and w2 == target_data.word_2:
            # 成功
            self.data[player_id].life += self.life_consume["aTrue"]
            target_data.life += self.life_variation["aTrue"]
            await ctx.send(f"攻撃成功！あなたのライフは`{self.data[player_id].life}`になりました。")
            await target_data.room.send(f"攻撃されました！あなたのライフは`{target_data.life}`になりました。")
        else:
            # 失敗
            self.data[player_id].life += self.life_consume["aFalse"]
            target_data.life += self.life_variation["aFalse"]
            await ctx.send(f"攻撃失敗。あなたのライフは`{self.data[player_id].life}`になりました。")
            await target_data.room.send(f"誰かの攻撃をブロックしました。あなたのライフは`{target_data.life}`になりました。")
            
        await self.alive(player_id, to)
        await self.turn(player_id)

    @commands.command(aliases=["b"])
    async def bomb(self, ctx, to: int):
        if not await self.p(ctx):
            return
        
        player_id = self.take(ctx)
        if self.data[player_id].life < -1 * self.life_consume["b"]:
            await ctx.reply("爆弾を使用するライフが足りません。")
            return
            
        if to < 0 or to >= len(self.data) or self.data[to].alive != 0:
            await ctx.reply("無効なターゲットです。")
            return
            
        target_data = self.data[to]
        self.data[player_id].life += self.life_consume["b"]
        
        await ctx.send(f"爆弾を仕掛けました。あなたのライフは`{self.data[player_id].life}`になりました。")
        await target_data.room.send("爆弾を仕掛けられました！")
        
        if target_data.has_defence:
            target_data.life += self.life_variation["bTrue"]
            target_data.has_defence = False
            await target_data.room.send("バリアが破壊されました！")
        else:
            target_data.life += self.life_variation["bFalse"]
        
        await target_data.room.send(f"あなたのライフは`{target_data.life}`になりました。")
        
        await self.alive(player_id, to)
        await self.turn(player_id)

    @commands.command(aliases=["c"])
    async def check(self, ctx, ch: int):
        if not await self.p(ctx):
            return
        
        player_id = self.take(ctx)
        
        self.data[player_id].life += self.life_consume["c"]
        await ctx.send(f"あなたのライフは`{self.data[player_id].life}`になりました。")
        
        if self.data[player_id].life <= 0:
            await self.alive(player_id, -1)
            await self.turn(player_id)
            return

        valid_targets = [i for i, d in enumerate(self.data) if i != player_id and d.alive == 0 and not d.has_defence]
        
        if not valid_targets:
            await ctx.reply("なんの成果も!!得られませんでした!!")
            await self.turn(player_id)
            return
        
        target_id = random.choice(valid_targets)
        target_data = self.data[target_id]
        
        if random.random() > fx(self.times):
            # 成功
            if ch == 1:
                await ctx.reply(f"プレイヤー`{target_id}`のword1は`{target_data.word_1}`です。")
            elif ch == 2:
                await ctx.reply(f"プレイヤー`{target_id}`のword2は`{target_data.word_2}`です。")
            else:
                await ctx.reply("`ch`は`1`または`2`である必要があります。")
        else:
            # 失敗
            await ctx.reply("なんの成果も!!得られませんでした!!")

        await self.alive(player_id, -1)
        await self.turn(player_id)

    @commands.command(aliases=["d"])
    async def defence(self, ctx):
        if not await self.p(ctx):
            return
        
        player_id = self.take(ctx)
        if self.data[player_id].life < -1 * self.life_consume["d"]:
            await ctx.reply("防御を使用するライフが足りません。")
            return
            
        if self.data[player_id].has_defence:
            await ctx.reply("すでに防御済みです。")
            return
            
        self.data[player_id].life += self.life_consume["d"]
        self.data[player_id].has_defence = True
        
        await ctx.reply(f"防御を張りました。あなたのライフは`{self.data[player_id].life}`になりました。")
        await self.alive(player_id, -1)
        await self.turn(player_id)

    @commands.command(aliases=["e"])
    async def eat(self, ctx):
        if not await self.p(ctx):
            return
        
        player_id = self.take(ctx)
        eat_limit = 5
        eat_bonus = 1
        prob_bonus = 0.1 # 10%

        adds = eat_bonus if random.random() <= prob_bonus else 0
        new_life = self.data[player_id].life + self.life_consume["e"] + adds

        if new_life <= eat_limit:
            self.data[player_id].life = new_life
            await ctx.reply(f"ライフが`{self.data[player_id].life}`になりました。")
        else:
            await ctx.reply(f"ライフの上限は`{eat_limit}`です。ライフは変わりませんでした。")
        
        await self.alive(player_id, -1)
        await self.turn(player_id)

    @commands.command(aliases=["f"])
    async def feint(self, ctx, to: int):
        if not await self.p(ctx):
            return
        
        player_id = self.take(ctx)
        if self.data[player_id].life < -1 * self.life_consume["f"]:
            await ctx.reply("フェイントを使用するライフが足りません。")
            return

        if to < 0 or to >= len(self.data) or self.data[to].alive != 0:
            await ctx.reply("無効なターゲットです。")
            return
            
        target_data = self.data[to]
        self.data[player_id].life += self.life_consume["f"]
        
        is_defenced = target_data.has_defence
        if is_defenced:
            target_data.has_defence = False
            await target_data.room.send("フェイントにより防御が解除されました。")
            await ctx.send(f"プレイヤー`{to}`の防御を解除しました。")
        else:
            await ctx.send(f"プレイヤー`{to}`にフェイントをかけました。")
            
        await ctx.send(f"あなたのライフは`{self.data[player_id].life}`になりました。")

        await self.alive(player_id, to)
        await self.turn(player_id)

    @commands.command()
    async def status(self, ctx):
        player_id = self.take(ctx)
        if player_id == -1:
            await ctx.reply("あなたはゲームに参加していません。")
            return

        user_data = self.data[player_id]
        await ctx.send(f"**プレイヤー`{player_id}`のステータス:**\n"
                       f"Word 1: `{user_data.word_1}`\n"
                       f"Word 2: `{user_data.word_2}`\n"
                       f"Life: `{user_data.life}`\n"
                       f"Defence: `{user_data.has_defence}`")

    @commands.command()
    async def debug(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            await ctx.reply("管理者のみが使用できます。")
            return
            
        output = [d.output_as_list() for d in self.data]
        await ctx.send(f"```[user_id, room_name, w1, w2, life, defence, alive, turn, set, display_id]\n{output}```")

    @commands.command()
    async def wd(self, ctx, cmd: str):
        if cmd.lower() == "help":
            await ctx.send("```?set [word2]\n?attack [相手:int] [word1] [word2]\n?bomb [相手:int]\n?check [word1or2:int]\n?defence\n?eat\n?feint [相手:int]\n?status```")
        else:
            await ctx.reply("コマンドが見つかりません。")

    # --- イベントリスナー ---
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.phase_game == 0:
            # ゲーム開始前はコマンド処理のみ
            await self.bot.process_commands(message)
            return

        # チャンネルがゲームカテゴリ内にない場合は無視
        if not message.channel.category or message.channel.category.id != self.category.id:
            await self.bot.process_commands(message)
            return
            
        # スレッド内でのプライベートメッセージの転送
        if isinstance(message.channel, discord.Thread):
            player_id = self.take(message)
            if player_id == -1: return

            if self.data[player_id].alive != 0:
                await message.reply("あなたはゲームオーバーのため、メッセージを送信できません。")
                return

            try:
                # 相手のスレッドIDを特定
                target_thread_id = -1
                for i in range(len(self.message_thread[player_id])):
                    if self.message_thread[player_id][i] and self.message_thread[player_id][i].id == message.channel.id:
                        target_thread_id = i
                        break

                if target_thread_id == -1:
                    print("Could not find matching thread ID.")
                    return
                    
                target_thread = self.message_thread[target_thread_id][player_id]
                if target_thread:
                    await target_thread.send(message.content)
                    await self.log_ch.send(f"from {player_id} to {target_thread_id}: {message.content}")
                else:
                    print(f"Target thread not found for player {target_thread_id}.")
            except Exception as e:
                print(f"Thread message forwarding error: {e}")
        
        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(WordGameCog(bot))