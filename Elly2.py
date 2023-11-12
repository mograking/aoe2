import os
import json
import sys
import logging
from pymongo import MongoClient
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

@tasks.loop(seconds=30)
async def getMatches():
    for i in ella.find({'subscribed':'true'}):
        r = requests.get('https://data.aoe2companion.com/api/matches?profile_ids='+i['relicId'] +'&search=&leaderboard_ids=&page=1').json()
        try:
            if 'matches' in r and len(r['matches'])>0 and not r['matches'][0]['finished']:
                lm = r['matches'][0]
                if not ella.find_one({'relicId':i['relicId'], 'lastMatchId':lm['matchId']}):
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

@client.event
async def on_message(message):
            if len(message.content) > 250 or message.author.bot:
                return

client.run(TOKEN)
