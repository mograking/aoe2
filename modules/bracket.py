
import json
import re
import requests
import apis_
import discord
import pandas as pd

import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv()

dbclient = MongoClient(os.getenv('LOCALMONGOURI'), int(os.getenv('LOCALMONGOPORT')))
ella = dbclient.aoe2bot.ella

class FAQMenu(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="FAQ", style=discord.ButtonStyle.blurple)
    async def FAQBox(self, interaction, button):
        await interaction.response.send_message("```1. Usage: '-bracket' or '-bracket minELO maxELO'. For example '-bracket 1000 1200'.\n2. To add yourself to this list, see Stats under '-help'. \n```")


def leftTrimEachLine(text):
    return re.sub(r'(\s|\|)+\n', '\n', text)

def getPlayerDataGuild(guild_id, minElo=0, maxElo=0):
    return ella.find({'discordId':{'$exists':'true'},'maxElo' :{'$ne' : 0} , 'relicId':{'$exists':'true'}, 'guildIds': {'$in' : [guild_id]}, 'elo' :{'$gte':minElo,'$lte':maxElo}}).sort('elo',-1) 

# for shorter display
def createELONameList(dbResponse):
    return [ (x['elo'], x['name'][:15] )  for x in dbResponse ]

def createNameELOList(dbResponse):
    return [ (x['name'], "{}-{}".format(x['elo'],x['maxElo']) ) for x in dbResponse ]

def getELOTableBracket(guild_id, minElo=0, maxElo=3000):
    return [ ('-1' if 'name' not in x else x['name'], "{}-{}".format(x['elo'],x['maxElo']) ) for x in ella.find({'discordId':{'$exists':'true'},'maxElo' :{'$ne' : 0} , 'relicId':{'$exists':'true'}, 'guildIds': {'$in' : [guild_id]}, 'elo' :{'$gte':minElo,'$lte':maxElo}}).sort('elo',-1) ]

def updatePersonalStatsGuildWise(guildId):
    list_of_relicIds = [ i['relicId'] for i in ella.find({'guildIds' : {'$in':[guildId]}}) ]
    try:
        r= requests.get(apis_.relicLinkPersonalStatsRelic("\",\"".join(list_of_relicIds))).json()
    except json.decoder.JSONDecodeError as exc:
        return
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
                ella.update_one({'discordId':member.id}, {'$push':{ 'guildIds':str(message.guild.id)} })

        if type(message.channel) is not discord.TextChannel and type(message.channel) is not discord.Thread:
            await message.channel.send('Not guild channel')
            return
        explicitELOs = re.compile('''[0-9]+''').findall(message.content)
        minELO = 0
        maxELO = 3000
        if len(explicitELOs) == 2:
            minELO= int(explicitELOs[0])
            maxELO= int(explicitELOs[1])
        bracketChannelNameRe = re.compile('''(lt|gt|[0-9]+)-[0-9]+''')
        if bracketChannelNameRe.findall(message.channel.name):
            limits = re.compile("[0-9]+").findall(message.channel.name)
            if message.channel.name.startswith('lt'):
                maxELO = int(limits[0])
            elif message.channel.name.startswith('gt'):
                minELO = int(limits[0])
            else:
                minELO, maxELO = [int(x) for x in limits]
        updatePersonalStatsGuildWise(str(message.guild.id))
        dbResponse = getPlayerDataGuild(str(message.guild.id), minElo=minELO, maxElo=maxELO)
        df = pd.DataFrame(createNameELOList(dbResponse), columns=['Alias','Current-Highest'])
        #df = pd.DataFrame(getELOTableBracket(str(message.guild.id),minElo=minELO,maxElo=maxELO), columns=['Alias','Current-Highest'])
        df.index+=1
        try:
            await message.channel.send("```\n{}\n```".format(df.to_markdown()) , view =FAQMenu())
        except discord.errors.HTTPException as exc:
            dbResponse = getPlayerDataGuild(str(message.guild.id), minElo=minELO, maxElo=maxELO)
            df = pd.DataFrame(createELONameList(dbResponse), columns=['ELO','Alias'])
            df.index += 1
            mdtext = df.to_markdown(tablefmt="plain")
            mdtext = leftTrimEachLine(mdtext)
            try:
                await message.channel.send("```\n{}\n```".format(mdtext), view=FAQMenu())
            except discord.errors.HTTPException as exc:
                await message.channel.send("```Too many members. Discord message limit exceeded.```", view=FAQMenu())
