import json
import apis_
from discord import Colour
import sys
import dataframe_image as dfi
import logging
import pandas as pd
import os
from discord.ext import tasks
import time
import requests
import threading
import re
import discord
from dotenv import load_dotenv
from pymongo import MongoClient
import urllib
from pymongo.server_api import ServerApi
load_dotenv()

logger = logging.getLogger('kuelflogger')
logging.basicConfig(filename='EL2.log', level = logging.ERROR)

def exceptionHandler(type, value, tb):
    logger.exception("Uncaught exception {0}".format(str(value)))

sys.excepthook = exceptionHandler

#usr = os.getenv('DBUSR')
#pwd = os.getenv('DBPWD')
#uri =os.getenv('MONGOFULLURI')
#dbclient = MongoClient(uri, server_api=ServerApi('1'))
dbclient = MongoClient(os.getenv('LOCALMONGOURI'), int(os.getenv('LOCALMONGOPORT')))
ella = dbclient.aoe2bot.ella

client = discord.Client(intents=discord.Intents.all())

def customLobbyMenu(author, gameId):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Join "+str(author)+"\'s game", url="http://"+str(os.getenv('SERVERHTTP'))+"?gameId="+str(gameId)+"&spectate=0"))
    view.add_item(discord.ui.Button(label="Spectate", url="http://"+str(os.getenv('SERVERHTTP'))+"?gameId="+str(gameId)+"&spectate=1"))
    return view

class StatusCode():
    def report(self):
        if self.code == -1:
            return "Invalid"
        elif self.code == 0:
            return "No effect"
        else:
            return self.message
        return ""

class helpMenu(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value=None

    @discord.ui.button(label = "Stats", style=discord.ButtonStyle.green)
    async def personalStats(self,interaction, button): 
        embed = discord.Embed(title="Manual: Personal Stats", description="Display AoE2 ladder rating of discord user")
        embed.add_field(name="Set your AoE profile", value="*!steamid <your steam id>* or *!relicid <link to your aoe2recs or aoe2companion profile>*", inline=False)
        embed.add_field(name="View personal stats", value="*!stats*", inline=False)
        embed.add_field(name="View User's stats", value="*!stats @User*",inline = False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label = "Sub", style=discord.ButtonStyle.blurple)
    async def subscribeMatchDetails(self,interaction, button): 
        embed = discord.Embed(title="Manual: Subscribe to match details", description="The bot will dm you your opponents ELO ratings during matches")
        embed.add_field(name="Subscribe", value="*!sub <link to your aoe2recs or aoe2companion profile>* or *!sub <relic id>*" ,inline=False)
        embed.add_field(name="Unsubscribe", value="*!unsub*",inline=False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label = "Guild leaderboard", style=discord.ButtonStyle.red)
    async def viewGuildLeaderboard(self,interaction, button): 
        embed = discord.Embed(title="Manual: Guild ELO leaderboard")
        embed.add_field(name="View", value="*!elo*" )
        embed.add_field(name="Add", value="*!add <link to aoe2recs or aoe2companion profile>* or *!add <relic id>*", inline=False)
        embed.add_field(name="Remove", value="*!remove <link to aoe2recs or aoe2companion profile>* or *!remove <relic id>*",inline=False)
        embed.add_field(name="Update info", value="*!update*",inline=False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label = "aoe2de:// links", style=discord.ButtonStyle.gray)
    async def customLobbyLinks(self,interaction, button): 
        embed = discord.Embed(title="Manual: Clickable aoe2de:// links", description="Join and spectate buttons for custom lobby links")
        embed.add_field(name="Why?", value="Discord doesn't allow aoe2de:// to be clickable. This bot creates a http link that redirects to the aoe2de link, thereby saving players from having to copy paste custom lobby links.", inline=False)
        embed.add_field(name="How?", value="Just drop a aoe2de:// link and the bot will do the rest.", inline=False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label = "Help", style=discord.ButtonStyle.gray)
    async def helpCommand(self,interaction, button): 
        embed = discord.Embed(title="Manual: Help", description="Use !help or mention the bot to pull up bot manual")
        await interaction.response.edit_message(embed=embed)

def displayStats(discordId):
    emb = discord.Embed(title="AoE2 Profile")
    player = ella.find_one({'discordId':discordId})
    if not player:
        emb.description = "No aoe2 profile associated with your discord id"
        emb.add_field(name="How to add aoe2 profile:", value="Type !steamid <your steam id> or !relicid <your aoe2 profile id>")
        return emb
    jdata = requests.get(apis_.aoe2companionProfile(player['relicId'])).json()
    if 'profileId' not in jdata:
        emb.description = "Invalid ID?"
        embed.add_field(name="Set your AoE profile", value="*!steamid <your steam id>* or *!relicid <link to your aoe2recs or aoe2companion profile>*", inline=False)
        return emb
    emb.title = "AoE2 " +jdata['name']
    emb.add_field(name="Profile", value=jdata['profileId'], inline=True)
    emb.add_field(name="Games", value=jdata['games'],inline=True)
    emb.add_field(name="AoE2Companion", value ="https://www.aoe2companion.com/profile/"+str(jdata['profileId']), inline=True)
    emb.colour = Colour.random()
    for ldrbrd in jdata['leaderboards']:
        emb.add_field(value=str(ldrbrd['rating'])+"-"+str(ldrbrd['maxRating']), name=ldrbrd['leaderboardName'],inline=True)
    emb.add_field(name="Add yours ", value="Type !steamid <your steam id> or !relicid <your aoe2 profile id>", inline=True)
    return emb

def registerId( authorId, steamId=-1, relicId =-1):
    status = StatusCode()
    r = {}
    if steamId != -1:
        r = requests.get(apis_.relicLinkPersonalStatsSteam(steamId)).json()
    elif relicId != -1:
        r = requests.get(apis_.relicLinkPersonalStatsRelic(relicId)).json()
    alias= ""
    try:
        relicId = str(r['statGroups'][0]['members'][0]['profile_id'])
        alias = r['statGroups'][0]['members'][0]['alias']
        #steamId = re.compile('[0-9]+').findall(r['statGroups'][0]['members'][0]['name'])[0]
    except KeyError as exc:
        status.code = -1
        return status
    ella.update_one({ 'relicId' : str(relicId) }, {'$set' : {'steamId' : steamId, 'discordId' : authorId, 'name' : alias} }, upsert=True)
    status.code = 1
    status.message = "Profile found : " + alias
    return status

def getPersonalStatRelic(relicId):
    elo =-1
    melo = -1
    alias = -1
    try:
        r = requests.get('https://aoe-api.reliclink.com/community/leaderboard/GetPersonalStat?title=age2&profile_ids=["'+str(relicId)+'"]').json()
        if r['result']['message'] == 'SUCCESS':
            alias = r['statGroups'][0]['members'][0]['alias']
            for x in r['leaderboardStats']:
                if x['leaderboard_id']==3:
                    elo = x['rating']
                    melo = x['highestrating']
            return (elo, melo, alias)
    except Exception as exc:
        print(exc)
        pass
    return (-1,-1)

def getELORelic(relicId):
    try:
        r = requests.get('https://aoe-api.reliclink.com/community/leaderboard/GetPersonalStat?title=age2&profile_ids=["'+str(relicId)+'"]').json()
        if r['result']['message'] == 'SUCCESS':
            for x in r['leaderboardStats']:
                if x['leaderboard_id']==3:
                    return (x['rating'], x['highestrating'])
    except Exception as exc:
        print(exc)
        pass
    return (-1,-1)

def updatePersonalStatsQuickOne(relicId):
    elo,melo,alias= getPersonalStatRelic(relicId)
    ella.update_one({'relicId' : relicId} , {'$set': {'elo':elo,'maxElo':melo, 'name':alias }})

def updatePersonalStatsMulti(guildId):
 threadList = []
 for i in ella.find({'guildIds' : {'$in':[guildId]}}):
    threadList += [ threading.Thread(target=updatePersonalStatsQuickOne, args = (i['relicId'],) ) ] 
 for i in range(len(threadList)):
    threadList[i].start()
 for i in range(len(threadList)):
    threadList[i].join()
 return

def updatePersonalStatsQuick(guildId):
 for i in ella.find({'guildIds' : {'$in':[guildId]}}):
    r = requests.get('https://data.aoe2companion.com/api/profiles/'+i['relicId']+'?profile_id='+i['relicId']+'&page=1').json()
    if 'error' not in r :
        try:
            updatedValues=dict()
            elo, maxElo = getELORelic(i['relicId'])
            updatedValues['elo'] = elo
            updatedValues['maxElo'] = maxElo
            updatedValues['steamId'] = r['steamId']
            updatedValues['country'] = r['country']
            updatedValues['games'] = r['games']
            updatedValues['name'] = r['name']        
            ella.update_one({'relicId' : i['relicId']} , {'$set': updatedValues})
        except Exception as exc:
            pass

def getName(relicId):
    try:
        return ella.find_one({'relicId':relicId})['name']
    except KeyError as exc:
        return ""

def regexGetId(string):
    return re.compile('[0-9][0-9][0-9][0-9][0-9]+').findall(string)[0]

def isRelicIdValid(profile_id):
    return 'error' not in requests.get('https://data.aoe2companion.com/api/profiles/'+profile_id+'?profile_id='+profile_id+'&page=1').json()

def removeIdFromGuild(relicId, guildId):
    status = StatusCode()
    if not isRelicIdValid(relicId):
        status.code = -1
    if not ella.find_one({'relicId': relicId, 'guildIds' : {'$in' : [guildId] } } ) :
        status.code = 0
    ella.update_many({'relicId':relicId},{ '$pull' : {'guildIds': guildId } } ) 
    status.code = 1
    status.message = 'Removed from guild list ' + getName(relicId)
    return status

def addIdToGuild(relicId, guildId):
    status = StatusCode()
    if not isRelicIdValid(relicId):
        status.code = -1
    if ella.find_one({'relicId': relicId, 'guildIds' : {'$in' : [guildId] } } ) :
        status.code = 0
    ella.update_one( {'relicId' :relicId} , {'$push' : {'guildIds' : guildId }} , upsert=True)
    status.code = 1
    status.message = 'Added to guild list ' + getName(relicId)
    return status

def addIdToTracking(relicId, discordId):
    relicId = str(relicId)
    status = StatusCode()
    if not isRelicIdValid(relicId):
        status.code = -1
    if ella.find_one({'relicId': relicId, 'discordId' : discordId } ) :
        status.code = 0
    ella.update_one({'relicId' : relicId} , { '$set': {'discordId' : discordId, 'subscribed': 'true'}} , upsert=True)
    status.code = 1
    status.message = 'AoE2 profile found! Added to subscription list ' + getName(relicId)
    return status

def removeTracking(discordId):
    status = StatusCode()
    if not ella.find_one({'discordId':discordId}):
        status.code = -1
    if ella.find_one({'discordId':discordId, 'subscribed':'false'}):
        status.code = 0
    ella.update_many({'discordId' : discordId} , { '$set' : {'subscribed' : 'false' } } )
    status.code = 1
    status.message = 'Removed from subscription list' 
    return status

def getELOTable(guild_id):
    return [ ('-1' if 'name' not in x else x['name'], -1 if 'elo' not in x else x['elo'], -1 if 'maxElo' not in x else x['maxElo'], -1 if 'relicId' not in x else x['relicId']) for x in ella.find({'name':{'$exists':'true'}, 'guildIds': {'$in' : [guild_id]}}).sort('elo',-1) ]

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if len(message.content) > 250 or message.author.bot:
        return

    if message.content.startswith('You okay?'):
        await message.channel.send('I\'m alright')
        return

    if message.content.startswith('!update'):
        starttime = time.time()
        updatePersonalStatsQuick(str(message.guild.id))
        endtime = time.time()
        await message.channel.send('ELO data updated. It took '+str(endtime-starttime))
        return

    if message.content.startswith('!mupdate'):
        starttime = time.time()
        updatePersonalStatsMulti(str(message.guild.id))
        endtime = time.time()
        await message.channel.send('ELO data updated. It took '+str(endtime-starttime))
        return

    if message.content.startswith('!trackme') or message.content.startswith('!sub'):
        relicId = regexGetId(message.content)
        if relicId == "":
            await message.channel.send("Try !sub <relic id> to get updates on your ongoing matches")
            return
        status =  addIdToTracking(relicId, message.author.id)
        await message.channel.send(status.report() + "\n Use !sub <relicid> to receive information on your ongoing matches")
        return

    if message.content.startswith('!untrackme') or message.content.startswith('!unsub'):
        status = removeTracking(message.author.id)
        await message.channel.send(status.report())
        return

    if message.content.startswith('!remove'):
        relicId = regexGetId(message.content)
        status = removeIdFromGuild(relicId,str(message.guild.id))
        await message.channel.send(status.report())
        return

    if message.content.startswith('!id') or message.content.startswith('!add'):
        relicId = regexGetId(message.content)
        status = addIdToGuild(relicId,str(message.guild.id))
        await message.channel.send(status.report())
        return


    if message.content.startswith('!elo'):
        df = pd.DataFrame(getELOTable(str(message.guild.id)), columns=['Alias','Current','Highest','RelicId'])
        df.index+=1
        dfi.export(df,'elo.png', table_conversion="matplotlib")
        await message.channel.send(file=discord.File('elo.png'))
        helptext = 'To add yourself to the guild\'s list type !add <your relic id> or !add <link to your profile on aoe2rec.com> \n'
        helptext += 'To remove yourself type !remove <id or link>\n'
        helptext += 'For example \'!add 15730812\' \n'
        await message.channel.send(helptext)
        return

    if message.content.startswith('!steamid'):
        steamId= regexGetId(message.content)
        status = registerId( message.author.id, steamId =steamId)
        await message.channel.send(status.report())

    if message.content.startswith('!relicid'):
        relicId= regexGetId(message.content)
        status = registerId( message.author.id, relicId =relicId)
        await message.channel.send(status.report())

    if message.content.startswith('!stats'):
        if len(message.mentions)>0:
            await message.channel.send(embed=displayStats(message.mentions[0].id))
        else: 
            await message.channel.send(embed=displayStats(message.author.id))

    aoe2de_pattern = re.compile('''aoe2de:\/\/0\/[0-9]+''')
    if aoe2de_pattern.findall(message.content):
        try:
            matchId = re.compile('[0-9][0-9][0-9][0-9]+').findall(message.content)[0]
        except IndexError as exc:
            return
        await message.channel.send(view = customLobbyMenu(message.author.name, matchId))
        return
        matchPoster = discord.Embed()
        matchPoster.title= "Join "+str(message.author.name)+ "\'s game (- u -)"
        matchPoster.url ="http://"+str(os.getenv('SERVERHTTP'))+"?gameId="+str(matchId)+"&spectate=0"
        matchPoster.description = '[Spectate](http://'+str(os.getenv('SERVERHTTP'))+'?gameId='+str(matchId)+'&spectate=1)\n'
        matchPoster.set_footer(text="How does this work? Discord doesn't allow aoe2de://0/ links to be clickable. But by redirecting from a http:// link this bot can save you some copy-paste work.")
        matchPoster.colour = Colour.random()
        await message.channel.send(embed=matchPoster)
        return

    if message.content.startswith('!help'):
        await message.channel.send(view=helpMenu(), embed=discord.Embed(title="Bot Manual", description="Use the buttons to see manual on different features"))
        return

    if message.content.startswith('!dbtest'):
        db_test_uri =os.getenv('MONGOFULLURI')
        db_test_dbclient = MongoClient(db_test_uri, server_api=ServerApi('1'))
        db_test_ella = db_test_dbclient.aoe2bot.ella

        st = time.time()
        for i in range(10):
            db_test_ella.find_one({'relicId':'15730812'})
        et = time.time()
        print('Remote database 10 find_one queries : {} \n'.format(et-st))

        st = time.time()
        for i in range(10):
            ella.find_one({'relicId':'15730812'})
        et = time.time()
        print('Local database 10 find_one queries : {} \n'.format(et-st))

        db_test_dbclient.close()
        return


client.run(os.getenv('DISCORD_TOKEN'))
