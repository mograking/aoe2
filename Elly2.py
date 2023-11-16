import os
import asyncio
import threading
import json
import sys
import logging
from pymongo import MongoClient
import time
import requests
import urllib
from pymongo.server_api import ServerApi
import discord
from discord.ext import tasks
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger('kuelflogger')
logging.basicConfig(filename='Elly2.log', level = logging.ERROR)

def exceptionHandler(type, value, tb):
    logger.exception("Uncaught exception {0}".format(str(value)))

sys.excepthook = exceptionHandler

usr = os.getenv('DBUSR')
pwd = os.getenv('DBPWD')
uri ='mongodb+srv://'+usr+':'+urllib.parse.quote(pwd)+'@cluster0.1ui1r.mongodb.net/?retryWrites=true&w=majority'
dbclient = MongoClient(uri, server_api=ServerApi('1'))
ella = dbclient.aoe2bot.ella

TOKEN = os.getenv('ELLY_DISCORD_TOKEN')

client = discord.Client(intents=discord.Intents.all())

def getELORelicString(relicId):
    try:
        r = requests.get('https://aoe-api.reliclink.com/community/leaderboard/GetPersonalStat?title=age2&profile_ids=["'+str(relicId)+'"]').json()
        if r['result']['message'] == 'SUCCESS':
            for x in r['leaderboardStats']:
                if x['leaderboard_id']==3:
                    return str(x['rating'])
    except Exception as exc:
        print(exc)
        pass
    return "NA"


def getMatchesOne(relicId, lastMatchId, discordId):
    r = requests.get('https://data.aoe2companion.com/api/matches?profile_ids='+relicId+'&search=&leaderboard_ids=&page=1').json()
    try:
        asyncio.run(client.get_user(440491679523274752).send('this is working'))
        if 'matches' in r and len(r['matches'])>0 and not r['matches'][0]['finished']:
            lm = r['matches'][0]
            if lastMatchId==-1 or lastMatchId != lm['matchId']:
                ella.update_one({'relicId':relicId}, {'$set':{'lastMatchId':lm['matchId']}})
                emb = discord.Embed(title=lm['name'])
                for t in lm['teams']:
                    for p in t['players']:
                        emb.add_field(name= p['name'], value = getELORelicString(p['profileId']), inline = False )
                print('Notifying :', relicId)
                asyncio.run(client.get_user(discordId).send(embed=emb))
    except KeyError as exc:
        pass
    except IndexError as exc:
        pass

@tasks.loop(seconds=30)
async def getMatchesMulti():
    starttime=time.time()
    threadPool=[]
    for i in ella.find({'subscribed':'true'}):
        threadPool += [ threading.Thread(target=getMatchesOne, args=(i['relicId'], -1 if 'lastMatchId' not in i else i['lastMatchId'], i['discordId'], ) ) ]
    for i in range(len(threadPool)):
        threadPool[i].start()
    for i in range(len(threadPool)):
        threadPool[i].join()
    endtime=time.time()
    print('multi took '+ str(endtime-starttime))
    return

@tasks.loop(seconds=30)
async def getMatches():
    for i in ella.find({'subscribed':'true'}):
        r = requests.get('https://data.aoe2companion.com/api/matches?profile_ids='+i['relicId'] +'&search=&leaderboard_ids=&page=1').json()
        try:
            if 'matches' in r and len(r['matches'])>0 and not r['matches'][0]['finished']:
                lm = r['matches'][0]
                if 'lastMatchId' not in i or i['lastMatchId'] != lm['matchId']:
                    ella.update_one({'relicId':i['relicId']}, {'$set':{'lastMatchId':lm['matchId']}})
                    emb = discord.Embed(title=lm['name'])
                    for t in lm['teams']:
                        for p in t['players']:
                            emb.add_field(name= p['name'], value = getELORelicString(p['profileId']), inline = False )
                    print('Notifying :', i['name'])
                    await client.get_user(i['discordId']).send(embed=emb)
        except Exception as exc:
            pass

@tasks.loop(seconds=30)
async def notifyTracked():
    for i in ella.find({'discordId' : {'$exists':'true'}, 'subscribed': 'true'}):
        if 'cMId' in i :
            if 'cMNotifiedId' not in i or i['cMId'] != i['cMNotifiedId']:
                try:
                    emb = discord.Embed(title=i['cMName'])
                    for y in range(len(i['cMPlayers'])):
                        emb.add_field(name= i['cMPlayers'][y] , value = getELORelicString(i['cMIds'][y]), inline = False )
                    ella.update_one( { 'relicId' : i['relicId'] } , { '$set' : { 'cMNotifiedId' : i['cMId'] } } )
                    print('Notifying :', i['name'])
                    await client.get_user(i['discordId']).send(embed=emb)
                except Exception as exc:
                    print(exc)
                    pass

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    #notifyTracked.start()
    getMatches.start()
    #getMatchesMulti.start()

@client.event
async def on_message(message):
            if len(message.content) > 250 or message.author.bot:
                return

client.run(TOKEN)
