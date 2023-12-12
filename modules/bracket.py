

import requests
import apis_
import discord
import dataframe_image as dfi
import pandas as pd

import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv()

dbclient = MongoClient(os.getenv('LOCALMONGOURI'), int(os.getenv('LOCALMONGOPORT')))
ella = dbclient.aoe2bot.ella

def getELOTableBracket(guild_id, minElo=0, maxElo=3000):
    return [ ('-1' if 'name' not in x else x['name'], -1 if 'elo' not in x else x['elo'], -1 if 'maxElo' not in x else x['maxElo'], -1 if 'relicId' not in x else x['relicId']) for x in ella.find({'discordId':{'$exists':'true'}, 'relicId':{'$exists':'true'}, 'guildIds': {'$in' : [guild_id]}, 'elo' :{'$gte':minElo,'$lte':maxElo}}).sort('elo',-1) ]

def updatePersonalStatsGuildWise(guildId):
    list_of_relicIds = [ i['relicId'] for i in ella.find({'guildIds' : {'$in':[guildId]}}) ]
    r= requests.get(apis_.relicLinkPersonalStatsRelic("\",\"".join(list_of_relicIds))).json()
    if r['result']['message'] == 'SUCCESS':
        statG2relicId =dict()
        statG2name =dict()
        for x in r['statGroups']:
            statG2relicId[x['id']] = str(x['members'][0]['profile_id'])
            statG2name[x['id']] = str(x['members'][0]['alias'])
        for x in r['leaderboardStats']:
            if x['leaderboard_id'] == 3:
                ella.update_one({'relicId': str(statG2relicId[x['statgroup_id']])},{'$set':{'name':statG2name[x['statgroup_id']],'elo':x['rating'], 'maxElo' : x['highestrating']}})
    return

def isCommand(message):
    return message.content.startswith('-bracket')

async def respond(message):
        if not message.guild:
            return
        for member in message.guild.members:
            if ella.find_one({'discordId':member.id, 'guildIds' :{'$nin' : [str(message.guild.id)]}} ) :
                ella.update_one({'discordId':str(member.id)}, {'$push':{ 'guildIds':str(message.guild.id)} })

        if type(message.channel) is not discord.TextChannel:
            await message.channel.send('Not guild channel')
        minELO, maxELO = message.channel.name.split('-')
        if not minELO or not maxELO or not maxELO.isnumeric() or ( not (minELO=='lt' or minELO=='gt') and not minELO.isnumeric() ):
            await message.channel.send('Guild name should be NUMBER-NUMBER or gt-NUMBER or lt-NUMBER.\n NUMBER should be between 0 and 3000')
        if minELO=='lt':
            minELO=0
            maxELO=int(maxELO)
        elif minELO=='gt':
            minELO=int(maxELO)
            maxELO=3000
        else:
            minELO=int(minELO)
            maxELO=int(maxELO)
        updatePersonalStatsGuildWise(str(message.guild.id))
        df = pd.DataFrame(getELOTableBracket(str(message.guild.id),minElo=minELO,maxElo=maxELO), columns=['Alias','Current','Highest','RelicId'])
        df.index+=1
        dfi.export(df,'elo.png', table_conversion="matplotlib")
        await message.channel.send(file=discord.File('elo.png'))
