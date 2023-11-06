import websocket
import ongoingMatches
import json
import base64
import _thread
from threading import Thread
import rel
import aoe2database as aoe2db
import dataframe_image as dfi
import pandas as pd
import os
import chinesehero
from discord.ext import tasks
import time
import requests
import re
import discord
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client(intents=discord.Intents.all())

MESSAGE_CACHE= []

LOBBIES = None
LOBBIES2 = None


# Ongoing matches 

DM_CACHE = set()

def embedMatchData(matchData):
    dm_Embed = discord.Embed(title="You are playing on ..." + matchData['map'])
    for p in matchData['players']:
        dm_Embed.add_field(name = p[0], value =aoe2db.getELOquick(str(p[2])) )
    return dm_Embed

def dmMatchData(matchData):
    print(matchData)
    msg = "You are playing ...\n"
    for p in matchData['players']:
        msg += str(p[0]) + '(' +str(p[1]) + ')' +'\n'
    msg += "On " + str(matchData['map'])
    return msg

def getPlayerNames(playersjson):
    if not playersjson:
        return []
    if len(playersjson) == 0:
        return []
    rv = []
    for x in playersjson:
        rv += [x['name']]
    return rv

def getInfo(gameId):
    if not LOBBIES:
        return None
    for x in LOBBIES:
        if x['match_id'] == gameId:
            return x
    return None

def dictToParams(params):
    queryString = []
    for param in params:
        queryString += [param+'='+params[param]]
    queryString = "&".join(queryString)
    queryString = '?'+queryString
    return  queryString

def createEmbed(gameId, player):
    #aoe2lobbyURL = "https://aoe2lobby.com/"
    awsServerURL = 'http://ec2-54-173-5-174.compute-1.amazonaws.com/'
    #joinURL = aoe2lobbyURL + "j/"
    #spectateURL = aoe2lobbyURL + "w/"

    qS=dict()
    qS['game_id']=gameId
    qS['spectate']="0"
    joinURL = awsServerURL + dictToParams(qS)
    qS['spectate']='1'
    specURL  = awsServerURL + dictToParams(qS)
    aoe_Embed = discord.Embed(title='''Join '''+player+''''s game (Redirects to aoe2de://0/'''+gameId+''')''')
    aoe_Embed.url=joinURL
    aoe_Embed.add_field(name="",value="[Spectate]("+specURL+")", inline=False)
    aoe_Embed.add_field(name="Match ID", value=gameId)
    info = getInfo(gameId)
    if info:
        if info['name']:
            aoe_Embed.add_field(name='Name', value=info['name'])
        if info['game_type']:
            aoe_Embed.add_field(name='Game Type', value=info['game_type'])
        if info['map_type']:
            aoe_Embed.add_field(name='Map Type', value=info['map_type'])
        if info['speed']:
            aoe_Embed.add_field(name='Speed', value=info['speed'])
        if info['num_slots']:
            aoe_Embed.add_field(name='Slots', value=info['num_slots'])
        if info['players']:
            playerlist = getPlayerNames(info['players'])
            aoe_Embed.add_field(name='Players', value=', '.join(playerlist))
    return aoe_Embed

async def getLobbies2():
    global LOBBIES2
    try:
        uri = 'https://aoe-api.reliclink.com/community/advertisement/findAdvertisements?title=age2' 
        r = requests.get(uri).json()
        LOBBIES2 = r
    except Exception as exc:
        pass

@tasks.loop(seconds=15)
async def detectLobbies():
    global LOBBIES2
    await getLobbies2()

async def getLobbies():
    global LOBBIES
    r = requests.get('https://aoe2api.dryforest.net/api/v3/lobbies').json()
    LOBBIES = r

async def updateMessage(index):
    global MESSAGE_CACHE
    for y in LOBBIES:
        if y['match_id']==MESSAGE_CACHE[index][0]:
            await MESSAGE_CACHE[index][2].edit(embed=createEmbed(MESSAGE_CACHE[index][0],MESSAGE_CACHE[index][1]))

#untrack after 10 minutes
@tasks.loop(seconds=600)
async def untrackMessages():
    global DM_CACHE
    global MESSAGE_CACHE
    MESSAGE_CACHE.clear()
    DM_CACHE.clear()

#update match info every 30 seconds
@tasks.loop(seconds=30)
async def updateMessages():
    await getLobbies()
    for index in range(len(MESSAGE_CACHE)):
        await updateMessage(index)




TRKS = set()
TRKL = []

@tasks.loop(seconds=30)
async def notifyTracked():
    j = aoe2db.getAllOngoing()
    for match in j:
        try:
            a1 = aoe2db.getAuthor(match['profile_id'])
            if a1 :
                await client.get_user(a1['author_id']).send(embed=embedMatchData(match))
        except Exception as exc:
            pass
        aoe2db.removeMatchON({'_id': match['_id']})

ws = Thread(target=ongoingMatches.restart)
ws.start()

@tasks.loop(seconds=1600)
async def refreshData():
    aoe2db.dumpON()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    #untrackMessages.start()
    #updateMessages.start()
    notifyTracked.start()
    #refreshData.start()

@client.event
async def on_message(message):
            global MESSAGE_CACHE
            if len(message.content) > 250 or message.author.bot:
                return

            aoe2de_pattern = re.compile('''aoe2de:\/\/0\/[0-9]+''')
            numbers_re = re.compile('[0-9]+')

            awsServerURL = 'http://ec2-54-173-5-174.compute-1.amazonaws.com/'

            creditCheckPattern = "!creditcheck"

            if message.content.startswith('!test'):
                user1 = client.get_user(message.author.id)
                await user1.send('hi')

            if message.content.startswith('!update'):
                await message.channel.send('updating ELO data')
                aoe2db.updateAllELOs()
                await message.channel.send('updating finished')

            if message.content.startswith('!trackme '):
                profile_id = list(filter(lambda x : len(x) > 4, numbers_re.findall(message.content) ))[0]
                if not aoe2db.isIDValid(profile_id):
                    await message.channel.send('Invalid ID')
                    return
                author_id = message.author.id
                aoe2db.addToTracking(profile_id, author_id)
                await message.author.send('Added to tracking list')
                return

            if message.content.startswith('!id '):
                profile_id = list(filter(lambda x : len(x) > 4, numbers_re.findall(message.content) ))[0]
                if not aoe2db.isIDValid(profile_id):
                    await message.channel.send('Invalid ID')
                    return
                if aoe2db.isIDpresent(profile_id,str(message.guild.id)):
                    await message.channel.send('ID already added to guild')
                    return 
                alias_ = aoe2db.addID(profile_id, str(message.guild.id))
                await message.channel.send('AoE2 profile found! Alias: '+alias_ + ' added to guild list')
                return

            if message.content.startswith('!elo'):
                df = pd.DataFrame(aoe2db.getELOforGuild(str(message.guild.id)), columns= ['Alias','Current','Running','Highest', 'Team'])
                df.index+=1
                dfi.export(df,'elo.png', table_conversion="matplotlib")
                await message.channel.send(file=discord.File('elo.png'))
                helptext = 'To add yourself to the guild\'s list type !id <your relic id> or !id <link to your profile on aoe2rec.com> \n'
                helptext += 'For example !id 15730812 \n'
                await message.channel.send(helptext)
                return

            if aoe2de_pattern.findall(message.content):
                player = message.author.name
                aoe_link = aoe2de_pattern.findall(message.content)[0]
                game_id = aoe_link[11:]
                emb = createEmbed(game_id,player)
                messageobj = await message.channel.send(embed=emb)
                MESSAGE_CACHE+=[[game_id,player,messageobj, time.time()]]

            if message.content.startswith(creditCheckPattern):
                if str(message.attachments) == "[]": # Checks if there is an attachment on the message
                    return
                else: # If there is it gets the filename from message.attachments
                    split_v1 = str(message.attachments).split("filename='")[1]
                    filename = str(split_v1).split("' ")[0]
                    if filename.endswith(".csv"): # Checks if it is a .csv file
                        await message.attachments[0].save(fp="CsvFiles/{}".format(filename))
                    errorIDs = chinesehero.runCreditCheckBulk()
                    await message.channel.send('hi errors at '+ ','.join(errorIDs), file=discord.File('hasPlayed10inlast30days.csv'))


client.run(TOKEN)
