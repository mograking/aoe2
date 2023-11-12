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

usr = os.getenv('DBUSR')
pwd = os.getenv('DBPWD')

uri ='mongodb+srv://'+usr+':'+urllib.parse.quote(pwd)+'@cluster0.1ui1r.mongodb.net/?retryWrites=true&w=majority'
dbclient = MongoClient(uri, server_api=ServerApi('1'))
ella = dbclient.aoe2bot.ella

client = discord.Client(intents=discord.Intents.all())

class StatusCode():
    def report(self):
        if self.code == -1:
            return "Invalid"
        elif self.code == 0:
            return "No effect"
        else:
            return self.message
        return ""

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
        emb.add_field(name="How to add aoe2 profile:", value="Type !steamid <your steam id> or !relicid <your aoe2 profile id>")
        return emb
    emb.title = "AoE2 " +jdata['name']
    emb.add_field(name="Profile", value=jdata['profileId'], inline=True)
    emb.add_field(name="Games", value=jdata['games'],inline=True)
    emb.add_field(name="AoE2Companion", value ="https://www.aoe2companion.com/profile/"+str(jdata['profileId']), inline=True)
    emb.colour = Colour.brand_red()
    for ldrbrd in jdata['leaderboards']:
        emb.add_field(value=str(ldrbrd['rating'])+"-"+str(ldrbrd['maxRating']), name=ldrbrd['leaderboardName'],inline=True)
    emb.add_field(name="Add yours ", value="Type !steamid <your steam id> or !relicid <your aoe2 profile id>", inline=True)
    return emb


def registerId( authorId, steamId=-1, relicId =-1):
    status = StatusCode()
    r = {}
    if steamId != -1:
        r = requests.get(apis_.relicLinkPersonalStatsSteam(steamId)).json()
    if relicId != -1:
        r = requests.get(apis_.relicLinkPersonalStatsRelic(relicId)).json()
    alias= ""
    try:
        relicId = r['statGroups'][0]['members'][0]['profile_id']
        alias = r['statGroups'][0]['members'][0]['alias']
        steamId = re.compile('[0-9]+').findall(r['statGroups'][0]['members'][0]['name'])[0]
    except KeyError as exc:
        status.code = -1
        return status
    ella.update_one({ 'relicId' : relicId }, {'$set' : {'steamId' : steamId, 'discordId' : authorId, 'name' : alias} }, upsert=True)
    status.code = 1
    status.message = "Profile found : " + alias
    return status

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
    return re.compile('[0-9]+').findall(string)[0]

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
                await message.author.send('I\'m alright')
                return

            if message.content.startswith('!update'):
                updatePersonalStatsQuick(str(message.guild.id))
                await message.author.send('ELO data updated')
                return

            if message.content.startswith('!trackme ') or message.content.startswith('!sub '):
                relicId = regexGetId(message.content)
                status=  addIdToTracking(relicId, message.author.id)
                await message.channel.send(status.report())
                return

            if message.content.startswith('!untrackme') or message.content.startswith('!unsub'):
                status = removeTracking(message.author.id)
                await message.channel.send(status.report())
                return

            if message.content.startswith('!remove '):
                relicId = regexGetId(message.content)
                status = removeIdFromGuild(relicId,str(message.guild.id))
                await message.channel.send(status.report())
                return

            if message.content.startswith('!id ') or message.content.startswith('!add '):
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
                helptext += 'For example !add 15730812 \n'
                await message.channel.send(helptext)
                return

            if message.content.startswith('!steamid'):
                steamId = re.compile('[0-9]+').findall(message.content)[0]
                status = registerId( message.author.id, steamId =steamId)
                await message.channel.send(status.report())

            if message.content.startswith('!relicid'):
                relicId = re.compile('[0-9]+').findall(message.content)[0]
                status = registerId( message.author.id, relicId =relicId)
                await message.channel.send(status.report())

            if message.content.startswith('!stats'):
                if len(message.mentions)>0:
                    await message.channel.send(embed=displayStats(message.mentions[0].id))
                else: 
                    await message.channel.send(embed=displayStats(message.author.id))


            aoe2de_pattern = re.compile('''aoe2de:\/\/0\/[0-9]+''')
            if aoe2de_pattern.findall(message.content):
                player = message.author.name
                aoe_link = aoe2de_pattern.findall(message.content)[0]
                game_id = aoe_link[11:]

client.run(os.getenv('DISCORD_TOKEN'))
