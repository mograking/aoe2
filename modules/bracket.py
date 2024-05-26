import json
import sqlite3
import re
import requests
import apis_
import pandas as pd
import discord

import os
from dotenv import load_dotenv
load_dotenv()


sqlc =sqlite3.connect('discordToAoe.db') 
cr = sqlc.cursor()

class FAQMenu(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="FAQ", style=discord.ButtonStyle.blurple)
    async def FAQBox(self, interaction, button):
        await interaction.response.send_message("```1. Use '-ranked 1000 1050' or '-teamranked 900 1000'.\n 2. See -help to add yourself to the list```")


def leftTrimEachLine(text):
    return re.sub(r'(\s|\|)+\n', '\n', text)

# for shorter display
def createELONameList(dbResponse):
    return [ (x['elo'], x['name'][:15] )  for x in dbResponse ]

def createNameELOList(dbResponse):
    return [ (x['name'], "{}-{}".format(x['elo'],x['maxElo']) ) for x in dbResponse ]

def getStats(listOfRelicIds, leaderboard="1v1"):
    leaderboardId = 3 if leaderboard == "1v1" else 4
    try:
        r= requests.get(apis_.relicLinkPersonalStatsRelic("\",\"".join(listOfRelicIds))).json()
    except json.decoder.JSONDecodeError as exc:
        return
    statsTable= []

    if r['result']['message'] == 'SUCCESS':
        statG2relicId =dict()
        statG2name =dict()
        for x in r['statGroups']:
            statG2relicId[x['id']] = str(x['members'][0]['profile_id'])
            statG2name[x['id']] = str(x['members'][0]['alias'])
        for x in r['leaderboardStats']:
            if x['leaderboard_id'] == leaderboardId:
                statsTable += [ {'name':statG2name[x['statgroup_id']], 'elo' : x['rating'], 'maxElo':x['highestrating']} ]
    return statsTable


def isCommand(message):
    return message.content.startswith('-bracket') or message.content.startswith('-ranked') or message.content.startswith('-teamranked')

async def respond(message):
        if not message.guild:
            return
        if message.content.startswith('-bracket') or message.content.startswith('-ranked'):
            leaderboard="1v1"
        elif message.content.startswith('-teamranked'):
            leaderboard="team"


        if type(message.channel) is not discord.TextChannel and type(message.channel) is not discord.Thread:
            await message.channel.send('Not guild channel')
            return

        listOfRelicId=[]
        for member in message.guild.members:
            #x = ella.find_one({'discordId':member.id})
            result = cr.execute('select * from d2a where discordid={};'.format(member.id)).fetchall()
            if len(result) > 0 : 
                listOfRelicId += [ str(result[0][1]) ]

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
        print(minELO, maxELO)
        dbResponse= sorted(filter(lambda x : x['elo']>minELO and x['elo']<maxELO, getStats(listOfRelicId, leaderboard=leaderboard)), key= lambda x: x['elo'], reverse=True)
        df = pd.DataFrame(createNameELOList(dbResponse), columns=['Alias','Current-Highest'])
        df.index+=1
        try:
            await message.channel.send("Leaderboard=**{}** \n ```\n{}\n```".format(leaderboard, df.to_markdown()) , view =FAQMenu())
        except discord.errors.HTTPException as exc:
            df = pd.DataFrame(createELONameList(dbResponse), columns=['ELO','Alias'])
            df.index += 1
            mdtext = df.to_markdown(tablefmt="plain")
            mdtext = leftTrimEachLine(mdtext)
            try:
                await message.channel.send("Leaderboard=**{}** \n```\n{}\n```".format(leaderboard, mdtext), view=FAQMenu())
            except discord.errors.HTTPException as exc:
                await message.channel.send("```Too many members. Discord message limit exceeded. Try a limited request like -ranked 900 1000 or -teamranked 500 1000```", view=FAQMenu())
