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
from dotenv import load_dotenv

load_dotenv('.env')
token = os.getenv("TOKEN")

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(
    command_prefix="?",
    case_insensitive=True,
    intents=intents
)

@bot.event
async def on_ready():
    print("Cleared to take off!")


#データベースの宣言まとめ
category:discord.CategoryChannel
log_act:discord.channel
log_ch:discord.channel
chat_room:discord.channel
data = []
user_ch = {}
message_thread = []
phase_game:int
phase_game = 0 #0は開始前 1はjoin後 2はset後
LifeConsume = {"aTrue":1,"aFalse":-1,"b":-3,"c":-1,"d":-2,"e":1,"f":-1}#ライフ消費量{a(成功),a(失敗),b,c,d,e,f}
LifeVariation = {"aTrue":-1,"aFalse":1,"bTrue":0,"bFalse":-2,"c":0,"d":0,"e":0,"f":0}#行動による他者のライフ変動{a(成功),a(失敗),b,c,d,e,f}
tmp_user:discord.user
shisha:int
shisha = 0
times = 1
ranking = []
data_send = []
join_ch:discord.channel

class UserData:
    __anon_user_id:discord.Member
    __room_id:discord.TextChannel
    __word_1:int
    __word_2:string
    __life:int
    __has_defence:bool
    __alive:int
    __is_turn:bool
    __has_set:bool
    __display:discord.Message

    def __init__(self) -> None:
        self.__anon_user_id = None
        self.__room_id = None
        self.__word_1 = None
        self.__word_2 = ""  #初期word2は空文字
        self.__life = 3  #初期ライフ
        self.__has_defence = False  #初期ディフェンスなし
        self.__alive = 0  #data[.].alive = 0 生きてる, 1 死亡後
        self.__is_turn = False  #行動できるか?
        self.__has_set = False  #setしたか
        self.__display = ""  #log_actのメッセージid

    @property
    def anon_user_id(self):
        return self.__anon_user_id
    @anon_user_id.setter
    def anon_user_id(self,input:discord.Member):
        try:
            self.__anon_user_id = input
        except ValueError:
            print(f"Type error in anon_user_id")
    @property
    def room_id(self):
        return self.__room_id
    @room_id.setter
    def room_id(self,input:discord.TextChannel):
        try:
            self.__room_id = input
        except ValueError:
            print(f"Type error in room_id")
    @property
    def word_1(self):
        return self.__word_1
    @word_1.setter
    def word_1(self,input:any):
        try:
            self.__word_1 = int(input)
        except ValueError:
            print(f"Type error in word_1")
    @property
    def word_2(self):
        return self.__word_2
    @word_2.setter
    def word_2(self,input:any):
        try:
            self.__word_2 = str(input)
        except ValueError:
            print(f"Type error in word_2")
    @property
    def life(self):
        return self.__life
    @life.setter
    def life(self,input:any):
        try:
            self.__life = int(input)
        except ValueError:
            print(f"Type error in life")
    @property
    def has_defence(self):
        return self.__has_defence
    @has_defence.setter
    def has_defence(self,input:any):
        try:
            self.__has_defence = strtobool(input)
        except ValueError:
            print(f"Type error in defence")
    @property
    def alive(self):
        return self.__alive
    @alive.setter
    def alive(self,input:any):
        try:
            self.__alive = int(input)
        except ValueError:
            print(f"Type error in alive")
    @property
    def is_turn(self):
        return self.__is_turn
    @is_turn.setter
    def is_turn(self,input:any):
        try:
            self.__is_turn = strtobool(input)
        except ValueError:
            print(f"Type error in is_turn")
    @property
    def has_set(self):
        return self.__has_set
    @has_set.setter
    def has_set(self,input:any):
        try:
            self.__has_set = strtobool(input)
        except ValueError:
            print(f"Type error in has_set")
    @property
    def display(self):
        return self.__display
    @display.setter
    def display(self,input:discord.Message):
        try:
            self.__display = input
        except ValueError:
            print(f"Type error in display")

    def dataMigration(self,source_data:list):
        #dataの長さと一致しなければ返す
        if len(source_data) != 9:
            print("dataMigration error")
            return
        #anon_user_idとroom_idはimportで使わないので省略
        try:
            self.__word_1 = int(source_data[2])
        except ValueError:
            print("input type error")
        try:
            self.__word_2 = str(source_data[3])
        except ValueError:
            print("input type error")
        try:
            self.__life = int(source_data[4])
        except ValueError:
            print("input type error")
        try:
            self.__has_defence = strtobool(source_data[5])
        except ValueError:
            print("input type error")
        try:
            self.__alive = int(source_data[6])
        except ValueError:
            print("input type error")
        try:
            self.__is_turn = strtobool(source_data[7])
        except ValueError:
            print("input type error")
        try:
            self.__has_set = strtobool(source_data[8])
        except ValueError:
            print("input type error")
        return

    def outputAsList(self):
        resp = [self.__anon_user_id,self.__room_id,self.__word_1,self.__word_2,self.__life,self.__has_defence,self.__alive,self.__is_turn,self.__has_set,self.__display]
        return resp

def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    if val in ('y', 'yes', 't', 'true', 'True', 'on', '1', 1):
        return True
    elif val in ('n', 'no', 'f', 'false', 'False', 'off', '0', 0):
        return False
    else:
        raise ValueError("invalid truth value {!r}".format(val))


###注意###このしたのtake()関数は選択制です 片方をコメントアウトして使ってください

#test = take(ctx)  とすると test にはctxを書いた人の登録されている部屋の番号が返ってきます
def take(ctx):
    return int(user_ch[ctx.author].name)
"""
#  test = take(ctx)  とすると test にはctxが書かれたチャンネルの番号が返ってきます
def take(ctx):
    return int(ctx.channel.name)
"""

#カウントダウンタイマーの関数　countdown_timer(n秒)
def countdown_timer(seconds):
    for i in range(seconds, 0, -1):
        time.sleep(1)
    print("The timer was ended.")

#名簿の受取,名前付きチャンネル立て,使い方表示,logチャンネル作成
@bot.command()
async def join(ctx,*member:discord.Member):
    if ctx.author.bot:
        return

    global phase_game
    if phase_game != 0:
        await ctx.reply("phase is incorrect")
        return

    members = []
    for m in member:
        members.append(m)

    if len(members)<2:
        await ctx.channel.send("Let's make friends !! (you cannot play alone)")
        return

    global join_ch
    join_ch = ctx.channel

    global category
    category = await ctx.guild.create_category(name="word")

    global log_act,log_ch,chat_room
    overwrites_={
        ctx.guild.default_role:discord.PermissionOverwrite(read_messages=False,send_messages=False)
    }
    log_act = await category.create_text_channel(name="log_act.",overwrites=overwrites_)
    log_ch = await category.create_text_channel(name="log_ch.",overwrites=overwrites_)
    chat_room = await category.create_text_channel(name="chat room")

    #０～membersの数-1までの整数をランダムに並び替える機構
    rand = []
    rand = list(range(len(members)))
    for i in range(len(members)):
        j = random.randint(0,len(members)-1)
        tmp = rand[i]
        rand[i]=rand[j]
        rand[j]=tmp
    print(f"rand...{rand}")#デバッグ用

    for i in range(len(members)**2):
        j =random.randint(0,len(members)-1)
        k =random.randint(0,len(members)-1)
        tmp = members[j]
        members[j] = members[k]
        members[k] = tmp

    global data,user_ch,message_thread
    message_thread = [[""]*len(members) for k in range(len(members))]
    #0,対応する人 1,対応する部屋 2,word1 3,word2 4,life 5,defence 6,alive 7,ターンの有無 8,set完了 9,ディスプレイid の順に格納
    for i in range(len(members)):
        data_user = UserData()
        if members.count(members[i]) == 1:
            data_user.anon_user_id = members[i]
            overwrites_={
                ctx.guild.default_role:discord.PermissionOverwrite(read_messages=False,send_messages=False),
                members[i]:discord.PermissionOverwrite(read_messages=True,send_messages=True)
            }
            channel = await category.create_text_channel(name=i,overwrites=overwrites_)
            data_user.room_id = channel
            data_user.word_1 = rand[i]

            for j in range(len(members)):
                if i != j:
                    thread = await channel.create_thread(name=j)
                    await thread.edit(invitable=False)
                    await thread.add_user(members[i])
                    message_thread[i][j] = thread
                    link = thread.mention #押したらスレッドへ移動できるリンクを取得
                    await channel.send(link)

        else:
            await ctx.channel.send("The same person has been entered multiple times.")
            await delete(ctx)
            return
        data.append(data_user)#data作成
        user_ch.setdefault(members[i],channel)#user_ch作成

    data[0].is_turn = True

    await log_act.send("room L D")
    for i in range(len(data)):
        data[i].display = await log_act.send(str(i)+" "+str(data[i].life)+" "+str(data[i].has_defence))

    global data_send
    data_send=[]
    for d in data:
        data_send.append(d.outputAsList()[2:9])#不要部分削除
    await log_act.send(str(data_send))
    await log_ch.send(str(data_send))

    for d in data:
        await log_ch.send(str(d.room_id.name)+" ... "+str(d.anon_user_id.name))

    for d in data:
        print(d.outputAsList())#デバッグ用

    phase_game = 1
    print("phase_game..."+str(phase_game))

    print("join was successed")

#tmpjoin import_dataによってimportされたdataをここで処理(dataに反映)
async def tmpjoin(ctx,tmp_data):
    if ctx.author.bot:
        return

    global phase_game
    if phase_game != 0:
        await ctx.reply("phase is incorrect.")
        return

    tmp_phase_game = tmp_data[0][0]
    tmp_data = tmp_data[1:]

    tmp_members = []
    for td in tmp_data:
        tmp = await bot.fetch_user(td[0])
        tmp_members.append(tmp)

    if len(tmp_members)<2:
        await ctx.channel.send("Let's make friends !! (you cannot play alone)")
        return

    global category
    category = await ctx.guild.create_category(name="word")

    global log_act,log_ch,chat_room
    overwrites_={
        ctx.guild.default_role:discord.PermissionOverwrite(read_messages=False,send_messages=False)
    }
    log_act = await category.create_text_channel(name="log_act.",overwrites=overwrites_)
    log_ch = await category.create_text_channel(name="log_ch.",overwrites=overwrites_)
    chat_room = await category.create_text_channel(name="chat room")

    global data,user_ch,message_thread
    message_thread = [[""]*len(tmp_members) for k in range(len(tmp_members))]
    for i in range(len(tmp_members)):
        #0,対応する人 1,対応する部屋 2,word1 3,word2 4,life 5,defence 6,alive 7,ターンの有無 8,set完了 9,ディスプレイid の順に格納
        data_user = UserData()
        if tmp_members.count(tmp_members[i]) == 1:
            data_user.anon_user_id = tmp_members[i]
            overwrites_={
                ctx.guild.default_role:discord.PermissionOverwrite(read_messages=False,send_messages=False),
                tmp_members[i]:discord.PermissionOverwrite(read_messages=True,send_messages=True)
            }
            channel = await category.create_text_channel(name=i,overwrites=overwrites_)
            data_user.room_id = channel
            data_user.dataMigration(tmp_data[i])
            for j in range(len(tmp_members)):
                if i != j:
                    thread = await channel.create_thread(name=j)
                    await thread.edit(invitable=False)
                    await thread.add_user(tmp_members[i])
                    message_thread[i][j] = thread
                    link = thread.mention #押したらスレッドへ移動できるリンクを取得
                    await channel.send(link)
        else:
            await ctx.channel.send("The same person has been entered multiple times.")
            await delete(ctx)
            return
        data.append(data_user)#data作成
        user_ch.setdefault(tmp_members[i],channel)#user_ch作成

    await log_act.send("room L D")
    for i in range(len(data)):
        data[i].display = await log_act.send(str(i)+" "+str(data[i].life)+" "+str(data[i].has_defence))

    global data_send
    data_send=[]
    for d in data:
        data_send.append(d.outputAsList()[2:9])#不要部分削除
    await log_act.send(str(data_send))
    await log_ch.send(str(data_send))

    for d in data:
        await log_ch.send(str(d.room_id.name)+" ... "+str(d.anon_user_id.name))
    print(f"tmp後data\n{data}")#デバッグ用
    phase_game = int(tmp_phase_game)
    print("tmp後phase_game..."+str(phase_game))

    print("tmpjoin was successed")

#チャンネル消去兼初期化
@bot.command()
async def delete(ctx):
    if ctx.author.bot:
        return

    global data,data_send,log_act,log_ch,chat_room

    await export_data(ctx)

    for d in data:
        try:
            await d.room_id.delete()
            del d
        except Exception as e:
            print(f"delete room error...{str(type(e))}")
    data = []
    data_send = []
    ranking = []

    try:
        await log_act.delete()
        log_act = None
    except Exception as e:
        print(f"delete log_act error...{str(type(e))}")
    try:
        await log_ch.delete()
        log_ch = None
    except Exception as e:
        print(f"delete log_ch error...{str(type(e))}")
    try:
        await chat_room.delete()
        chat_room = None
    except Exception as e:
        print(f"delete chat_room error...{str(type(e))}")
    global category
    try:
        await category.delete()
        category = None
    except Exception as e:
        print(f"delete category error...{str(type(e))}")

    global phase_game
    phase_game = 0
    print("delete was successed")

#game中のデータ変更
@bot.command()
async def cheat(ctx,cmd:str,to:int,effect:int):
    if ctx.channel != chat_room:
        await ctx.reply("You can not use this command on this channel.")
    else:
        if cmd == "help":
            await ctx.reply("cheat.cmd_index```?cheat alive (to) (effect_0:living,1:dead)\n?cheat fixlife (to) (new life)\n?cheat fixdefence (to) (effect_0:no-defenced,1:defenced)\n?cheat turn (next turn's player) activate```")
        elif cmd == "alive":
            if effect == 0:
                data[to].alive = 0
                data[to].life = 1
                await ctx.channel.send("player"+str(to)+" came back to the game.")
            elif effect == 1:
                data[to].alive = 1
                data[to].life = 0
                await ctx.channel.send("player"+str(to)+" was killed.")
                alive(to,-1)
        elif cmd == "fixlife":
            data[to].life = effect
            await ctx.channel.send("player"+str(to)+"'s life was changed to "+str(effect)+".")
        elif cmd == "fixdefence":
            if effect == 0:
                data[to].has_defence = False
                await ctx.channel.send("player"+str(to)+" lost a defence.")
            elif effect == 1:
                data[to].has_defence = True
                await ctx.channel.send("player"+str(to)+" got a defence.")
        elif cmd == "turn":
            await turn((to-1))

#setコマンド
@bot.command()
async def set(ctx,*,word2:str):
    if ctx.author.bot:
        return

    global phase_game
    if phase_game != 1:
        await ctx.send("phase is incorrect.")
        return

    global log_act
    global data
    data[take(ctx)].word_2 = word2
    print(f"{take(ctx)}'s word2 is {data[take(ctx)].word_2}")

    await log_act.send("word2_player"+str(take(ctx))+":"+word2)
    await ctx.channel.send("Preparation is complete. Please wait until the game starts.")
    await ctx.channel.send("Your word1 is '"+str(data[take(ctx)].word_1)+"',word2 is '"+str(data[take(ctx)].word_2)+"'.")

    data[take(ctx)].has_set = True#set完了

    ch:bool
    ch = True
    for d in data:
        ch = (ch and (d.has_set == True)) #set完了なら積をとっても1になるはず

    if ch:
        if phase_game == 1:
            for d in data:
                await d.room_id.send("ｺﾉﾓﾝﾀﾞｲﾊ 30ﾋﾞｮｳｺﾞﾆ ﾊｼﾞﾏﾘﾏｽ")
            #for i in range(30, 0, -1):#30秒タイマー
            #    time.sleep(1)
            for d in data:
                await d.room_id.send("Game start!")
            await log_act.send("0's turn!")
            await data[0].room_id.send("Your turn!")
            phase_game = 2

    print(f"is set all clear ?...{ch}")
    print("set was successed")

#終了
async def fin():
    global log_act,log_ch,chat_room,data,ranking

    for i in range(len(data)):
        if data[i].life > 0:
            ranking.append(data[i].anon_user_id)
#勝者のlifeが残っているときにランキングに入れる。

    await log_act.send("FIN")
    await log_ch.send("FIN")
    await chat_room.send("FIN")
    for d in data:
        await d.room_id.send("FIN")

    await chat_room.send("Ranking is...")
    for j in range(len(data)-1):
        jRank = ranking.pop(0)
        await chat_room.send("No."+str(len(ranking)+1)+":"+str(jRank))
    await chat_room.send("And the champion is")
    for t in range(3, 0, -1):#3秒タイマー
        time.sleep(1)
        await chat_room.send("     ・")
    await chat_room.send(str(ranking.pop(0))+"!!!")


#次のターンへ移動
async def turn(now:int):

    global times
    global data

    data[now].is_turn = False
    next:int
    next = (now + 1) % len(data)
    data[next].is_turn = True
    times = times + 1
    if len(ranking)+1 >= len(data):
        await fin()
    #生存者1人以下でfin
    elif data[next].alive != 0:
        await turn(next)
    else:
        await data[next].room_id.send("Your turn!")
        if data[now].alive == 0:
            await data[now].room_id.send("Your turn was ended.")
        await log_act.send(str(next)+"'s turn!")
        return
    #finしないなら次のプレイヤーのターン

#生死判定
#data[.].alive = 0 生きてる, 1 死亡後

#toが存在しないもの
    #alive(take(ctx),-1)
#toが存在するもの
    #alive(take(ctx),to)
async def alive(by:int,to:int):
    global data,ranking
    if to >= 0 and to != by and int(data[to].alive) == 0:
#実在するplayerか判定
#自分への行動を除外
#死者への行動を除外、いらないけど念のため残してほしい

        await data[to].display.edit(content=str(str(to)+" "+str(data[to].life)+" "+str(data[to].has_defence)))

        if int(data[to].life) <= 0:
            data[to].alive = 1
            await data[to].room_id.send("You are dead!")
            await log_act.send(str(to)+" is dead!")
            ranking.append(data[to].anon_user_id)
            await log_act.set_permissions(data[to].anon_user_id,read_messages=True,send_messages=False)
            await log_ch.set_permissions(data[to].anon_user_id,read_messages=True,send_messages=False)
            await chat_room.set_permissions(data[to].anon_user_id,read_messages=True,send_messages=False)

    await data[by].display.edit(content=str(str(by)+" "+str(data[by].life)+" "+str(data[by].has_defence)))

    if int(data[by].life) <= 0:
        data[by].alive = 1
        await data[by].room_id.send("You are dead!")
        await log_act.send(str(by)+" is dead!")
        ranking.append(data[by].anon_user_id)
        await log_act.set_permissions(data[by].anon_user_id,read_messages=True,send_messages=False)
        await log_ch.set_permissions(data[by].anon_user_id,read_messages=True,send_messages=False)
        await chat_room.set_permissions(data[by].anon_user_id,read_messages=True,send_messages=False)

#コマンドが実行可能な人か判断
async def p(ctx):
    ch = True
    #False で実行不可
    a = [True]*4

    if ctx.author.bot:
        a[0] = False

    global user_ch,data
    if data[take(ctx)].alive != 0:
        a[1] = False

    if data[take(ctx)].is_turn == False:
        a[2] = False

    global phase_game
    if phase_game != 2:
        a[3] = False

    #すべてTrueで通過
    print(a)
    for i in a:
        ch = ch and i

    if ch != True:
        await ctx.reply("You do not have the authority to take that action.")

    return ch


#a-f定義
@bot.command(aliases = ["a"])
async def attack(ctx,to:int,w1:str,*,w2:str):

    if True != await p(ctx):
        return

    try:
        if data[to].life > 0:
            if (w1 == str(data[to].word_1)) & (w2 == data[to].word_2):
                #成功パターン
                #攻撃者ライフ設定
                MyNewLife = data[take(ctx)].life + LifeConsume["aTrue"]
                data[take(ctx)].life = MyNewLife
                #被攻撃者ライフ設定
                ToNewLife = data[to].life + LifeVariation["aTrue"]
                data[to].life = ToNewLife

                await ctx.channel.send("Your attack was successed.")
                await ctx.channel.send("The remaining life has changed to "+str(data[take(ctx)].life)+".")
                await data[to].room_id.send("You were attacked.")
                await data[to].room_id.send("The remaining life has changed to "+str(data[to].life)+".")
                await log_act.send(str(take(ctx))+"'s attack was successed.\nto:"+str(to)+"w1:"+str(w1)+"w2:"+str(w2)+"\n"+str(take(ctx))+"'s life became "+str(MyNewLife)+", "+str(to)+"'s life became "+str(ToNewLife))

            else:
                #失敗パターン
                #攻撃者ライフ設定
                MyNewLife = data[take(ctx)].life + LifeConsume["aFalse"]
                data[take(ctx)].life = MyNewLife
                #被攻撃者ライフ設定
                ToNewLife = data[to].life + LifeVariation["aFalse"]
                data[to].life = ToNewLife

                await ctx.channel.send("Your attack failed.")
                await ctx.channel.send("The remaining life has changed to "+str(data[take(ctx)].life)+".")
                await data[to].room_id.send("An attack by someone was blocked.")
                await data[to].room_id.send("The remaining life has changed to "+str(data[to].life)+".")
                await log_act.send(str(take(ctx))+"'s attack was rejected.\nto:"+str(to)+"  w1:"+str(w1)+"  w2:"+str(w2)+"\n"+str(take(ctx))+"'s life became "+str(MyNewLife)+", "+str(to)+"'s life became "+str(ToNewLife))


            await alive(take(ctx),to)
            await turn(take(ctx))


        else:
            await ctx.reply("Shooting a corpse is not gentlemanly.")

    except Exception as e:
            print(f"attack error...{str(type(e))}")
            await ctx.reply("Cannot be executed. Please check if your input is correct.")

    print("attack was successed")

@bot.command(aliases = ["b"])
async def bomb(ctx,to:int):

    if True != await p(ctx):
        return

    try:
        if data[to].life > 0:
            if data[take(ctx)].life >= -1*LifeConsume["b"]:
                #攻撃者ライフ設定
                MyNewLife = data[take(ctx)].life + LifeConsume["b"]
                data[take(ctx)].life = MyNewLife
                await ctx.channel.send("Your bomb was exploded.")
                await ctx.channel.send("The remaining life has changed to "+str(data[take(ctx)].life)+".")
                await data[to].room_id.send("You were exposed to a bomb.")
                if data[to].has_defence == True:
                    #defenced
                    ToNewLife = data[to].life + LifeVariation["bTrue"]
                    data[to].life = ToNewLife
                    data[to].has_defence = False
                    await data[to].room_id.send("Your barrier was broken!")
                    await data[to].room_id.send("The remaining life has changed to "+str(data[to].life)+".")
                    await log_act.send(str(to)+"'s defence was broken.")
                    await log_act.send(str(take(ctx))+"'s bomb was exploded to "+str(to)+".\n"+str(take(ctx))+"'s life became "+str(MyNewLife)+", "+str(to)+"'s life became "+str(ToNewLife))
                else:
                    #undefenced
                    ToNewLife = data[to].life + LifeVariation["bFalse"]
                    data[to].life = ToNewLife
                    await data[to].room_id.send("The remaining life has changed to "+str(data[to].life)+".")
                    await log_act.send(str(take(ctx))+"'s bomb was exploded to "+str(to)+".\n"+str(take(ctx))+"'s life became "+str(MyNewLife)+", "+str(to)+"'s life became "+str(ToNewLife))
                
            else:
                await ctx.reply("You do not have enough life for bomb.")
                return
        else:
            await ctx.reply("Shooting a corpse is not gentlemanly.")

    except Exception as e:
            print(f"bomb error...{str(type(e))}")
            await ctx.reply("Cannot be executed. Please check if your input is correct.")
            return

    await alive(take(ctx),to)
    await turn(take(ctx))

    print("bomb was successed")

@bot.command(aliases = ["c"])
async def check(ctx,ch:int):

    if True != await p(ctx):
        return

    global LifeConsume
    global LifeVariation
    global times

    koho = []
    k:int
    k=0
    b:bool
    b=True
    for i in range(len(data)):
        if i != take(ctx) and data[i].alive == 0 and data[i].has_defence != True:#打った本人でない 死んでない dしてない
            koho.append(i)
            k+=1

    data[take(ctx)].life = data[take(ctx)].life + LifeConsume["c"]
    await log_act.send(str(take(ctx))+"'s life become "+str(data[take(ctx)].life))

    if k == 0:
        await ctx.reply("なんの成果も!!得られませんでした!!")

        b = False #falseならcheck失敗

    if b != False:
        i = random.randint(0,k-1)
        i = koho[i]

        p_fail = random.random()
        rot = fx(times)

        print(p_fail)
        print(rot)
        print(times)

        if p_fail>rot:
            #成功
            if ch == 1:
                await ctx.reply(str(i)+"'s word1 is ``` "+str(data[i].word_1)+" ```")
                await ctx.reply(str(data[i].word_1))
                await log_act.send(str(take(ctx))+" check the word1 of "+str(i))

            if ch == 2:
                await ctx.reply(str(i)+"'s word2 is ``` "+str(data[i].word_2)+" ```")
                await ctx.reply(str(data[i].word_2))
                await log_act.send(str(take(ctx))+" check the word2 of "+str(i))
        else:
            #失敗
            await ctx.reply("なんの成果も!!得られませんでした!!")

    await ctx.channel.send("The remaining life has changed to "+str(data[take(ctx)].life)+".")

    await alive(take(ctx),-1)
    await turn(take(ctx))

    print("check was successed")

@bot.command(aliases = ["d"])
async def defence(ctx):

    if True != await p(ctx):
        await ctx.reply("You do not have the authority to take that action.")
        return

    global LifeConsume
    global LifeVariation

    if data[take(ctx)].life < -1*LifeConsume["d"]:
        await ctx.reply("You do not have enough life for defence.")
        return

    if data[take(ctx)].has_defence == True:
        ctx.reply("You have defenced!")
        return

    data[take(ctx)].life = data[take(ctx)].life + LifeConsume["d"]
    await log_act.send(str(take(ctx))+"'s life become "+str(data[take(ctx)].life))

    data[take(ctx)].has_defence = True
    await ctx.reply("Your defence was "+str(data[take(ctx)].has_defence))
    await log_act.send(str(take(ctx))+"made defence")
    await ctx.channel.send("The remaining life has changed to "+str(data[take(ctx)].life)+".")

    await alive(take(ctx),-1)
    await turn(take(ctx))

    print("deffence was successed")

@bot.command(aliases = ["e"])
async def eat(ctx):

    if True != await p(ctx):
        return

    e_limit = 5
    e_bonus = 1
    P_bonus = 10#%表示
    adds = 0
    if random.randint(1,100) <= P_bonus:#抽選部分
        adds = e_bonus
    await ctx.channel.send("You should be able to get just a little more life!!")

    NewLife = data[take(ctx)].life + LifeConsume["e"] + adds

    if NewLife <= e_limit : #eのライフ上限
        data[take(ctx)].life = NewLife
        await ctx.channel.send("The remaining life has changed to "+str(NewLife)+".")
    else:
        await ctx.channel.send("The maximum life limit for eat is "+str(e_limit)+". Your remaining life is "+str(data[take(ctx)].life)+".")

    await log_act.send(str(take(ctx))+" got a little full\nLife became "+str(NewLife))

    await alive(take(ctx),-1)
    await turn(take(ctx))

    print("eat was successed")

@bot.command(aliases = ["f"])
async def feint(ctx,to:int):

    if True != await p(ctx):
        return

    global LifeConsume
    global LifeVariation

    if data[take(ctx)].life < -1*LifeConsume["f"]:
        await ctx.reply("You do not have enough life for feint.")
        return

    if data[to].life > 0:
        data[take(ctx)].life = data[take(ctx)].life + LifeConsume["f"]
        data[to].life = data[to].life + LifeVariation["f"]
        await log_act.send(str(take(ctx))+"'s life become "+str(data[take(ctx)].life))
        await log_act.send(str(to)+"'s life become "+str(data[to].life))

        if data[to].has_defence == True:#dあったなら
            await ctx.reply("You made a feint at "+str(to)+".")
            data[to].has_defence = False
            await log_act.send(str(to)+"was broken the defence")
            await data[to].room_id.send("Your defence was broken!")
        else:
            await ctx.reply("You made a feint at "+str(to)+".")

        await ctx.channel.send("The remaining life has changed to "+str(data[take(ctx)].life)+".")
    else:
        await ctx.reply("Shooting a corpse is not gentlemanly.")

    await alive(take(ctx),to)
    await turn(take(ctx))

    print("feint was successed")

@bot.command()
async def status(ctx):

    if ctx.author.bot:
        return

    if phase_game == 2:
        #対応する人 対応する部屋 word1 word2 life defence alive ターンの有無 set完了 の順に格納
        await ctx.send("word1 : `"+str(data[take(ctx)].word_1)+"`")
        await ctx.send("word2 : `"+str(data[take(ctx)].word_2)+"`")
        await ctx.send("life : `"+str(data[take(ctx)].life)+"`")
        await ctx.send("defence : `"+str(data[take(ctx)].has_defence)+"`")

#c失敗の確率
def fx(x:int):#xにtimesを代入
    ans = 1/(3*(math.ceil(x/len(data))))
    return ans

@bot.command()
async def gx(x:int):#xにtimesを代入
    print(x)

@bot.command()
async def debug(ctx):
    global data_send
    data_send=[]
    for d in data:
        d = d.outputAsList()
        data_send.append(d[2:9])#不要部分削除
    await ctx.send("```[word1, word2, life, defence, alive, turn, set]```")
    await ctx.send(data_send)

#tell(on_message)
@bot.event
async def on_message(ctx):
    global category,data,message_thread,log_ch
    if ctx.author.bot:
        return

    if phase_game != 0:
        if ctx.channel.category != category:
            return

    if type(ctx.channel) == discord.Thread:
        if data[take(ctx)].alive == 0:
                try:
                    await message_thread[message_thread[take(ctx)].index(ctx.channel)][take(ctx)].send(ctx.content)
                    #.indexで誰に送るかを把握し、逆順の配列に送信する。
                    await log_ch.send("from "+str(take(ctx))+"   "+"to "+str(message_thread[take(ctx)].index(ctx.channel))+"   "+ctx.content)
                    return
                except Exception as e:
                    print(f"Thread error...{e}")

    try:
        await bot.process_commands(ctx)
    except Exception as e:
        print(f"command error...{e}")

@bot.command()
async def export_data(ctx):
    global data,phase_game,join_ch
    # タイムスタンプを用いてユニークなファイル名を作成
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    file_path = f'channels_{timestamp}.csv'

    # ファイルにチャンネル情報を書き込む
    #"user.id","room_name","w1","w2","life","defence","alive","turn","set?"の順に格納
    #displayはtxtの中に入ってません
    with open(file_path, 'w', encoding='utf-8',newline='') as f:
        writer = csv.writer(f)
        writer.writerow([phase_game])
        for d in data:
            d = d.outputAsList()
            writer.writerow([d[0].id,d[1].name,d[2],d[3],d[4],d[5],d[6],d[7],d[8]])

    await join_ch.send(file=discord.File(file_path))

    os.remove(file_path)

@bot.command()
async def import_data(ctx):
    global join_ch
    if not ctx.message.attachments:
        await ctx.send("The file is not defined.")
        return

    attachment = ctx.message.attachments[0]
    file_path = f'tmp_{attachment.filename}'

    async with aiohttp.ClientSession() as session:
        async with session.get(attachment.url) as response:
            if response.status == 200:
                with open(file_path, 'wb') as f:
                    f.write(await response.read())

    # ファイルを処理する
    with open(file_path, 'r', encoding='utf-8',newline='') as f:
        # ここでファイルの内容を処理します
        reader = csv.reader(f)
        tmp_data = [row for row in reader]
        print(f"tmp_data\n{tmp_data}")

    await tmpjoin(ctx,tmp_data)
    join_ch = ctx.channel   

    os.remove(file_path)
    await ctx.send(f"{attachment.filename} is complete.")

@bot.command()
async def wd(ctx,cmd:str):
    
    if cmd == "help":
        await ctx.send("```?set [word2:str]\n?attack [相手:int] [word1] [word2]\n?bomb [相手:int]\n?check [word1or2:int]\n?defence\n?eat\n?feint [相手:int]\n?status```")

@bot.command()
async def ping(ctx):
    if ctx.author.bot:
        return
    file = os.path.basename(__file__)
    await ctx.reply(f"pong [{file}]")

bot.run(token)