import requests
import sqlite3
import re
import json
import discord
import apis_
import os
from dotenv import load_dotenv
load_dotenv()

sqlc =sqlite3.connect('discordToAoe.db') 
cr = sqlc.cursor()

class StatsMenu(discord.ui.View):
    def __init__(self, discordId):
        super().__init__()
        self.value=None
        self.discordId=discordId
        self.player = {}
        res = cr.execute('select * from d2a where discordid={};'.format(discordId)).fetchall()
        self.player['relicId'] = res[0][1]

    @discord.ui.button(label="Detailed", style=discord.ButtonStyle.blurple)
    async def personalStats(self, interaction, button):
        discordId = self.discordId
        embed = discord.Embed(title="AoE2 Profile")
        player = self.player
        if not player:
            embed.description = "Invalid ID?"
            embed.add_field(name="Set your AoE profile", value="*-steamid <your steam id>* or *-relicid <link to your aoe2recs or aoe2companion profile>*", inline=False)
            await interaction.response.edit_message(embed=embed)
            return
        jdata = requests.get(apis_.aoe2companionProfile(player['relicId'])).json()
        if 'profileId' not in jdata:
            embed.description = "Invalid ID?"
            embed.add_field(name="Set your AoE profile", value="*-steamid <your steam id>* or *-relicid <link to your aoe2recs or aoe2companion profile>*", inline=False)
            await interaction.response.edit_message(embed=embed)
            return
        embed.title = jdata['name']
        embed.add_field(name="Profile", value=jdata['profileId'], inline=True)
        embed.add_field(name="Games", value=jdata['games'],inline=True)
        embed.add_field(name="AoE2Companion", value ="https://www.aoe2companion.com/profile/"+str(jdata['profileId']), inline=False)
        embed.colour = discord.Colour.random()
        for ldrbrd in jdata['leaderboards']:
            embed.add_field(value="{}-{} [ W {} L {} ]".format(str(ldrbrd['rating']),str(ldrbrd['maxRating']), str(ldrbrd['wins']), str(ldrbrd['losses'])), name=ldrbrd['leaderboardName'],inline=False)
        embed.add_field(name="Latest ELO changes", value="", inline=False)
        for rtngs in jdata['ratings']:
            lastFewRatings= [ str(r['rating']) for r in rtngs['ratings'][5::-1] ]
            if len(lastFewRatings) < 3:
                continue
            embed.add_field(name=rtngs['leaderboardName'], value="**  -> **".join(lastFewRatings), inline=False)
        embed.add_field(name="Add or Change", value="Type -steamid <your steam id> or -relicid <your aoe2 profile id>", inline=False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Last Match", style=discord.ButtonStyle.green)
    async def lastMatchData(self, interaction, button):
        embed=discord.Embed(title="Last Match")
        player=self.player
        if not player:
            embed.description = "Invalid ID?"
            embed.add_field(name="Set your AoE profile", value="*-steamid <your steam id>* or *-relicid <link to your aoe2recs or aoe2companion profile>*", inline=False)
            await interaction.response.edit_message(embed=embed)
            return
        jdata = requests.get(apis_.aoe2companionMatches(player['relicId'])).json()
        if 'matches' not in jdata or len(jdata['matches'])==0:
            embed.description = "No data"
            await interaction.response.edit_message(embed=embed)
            return
        lastMatch = jdata['matches'][0]
        victory=False
        alias=""
        embed.add_field(name="Map", value=lastMatch['mapName'],inline=True)
        embed.add_field(name="Ladder", value=lastMatch['leaderboardId'],inline=True)
        for team_ in lastMatch['teams']:
            embed.add_field(name="Team", inline=False, value="")
            for player_ in team_["players"]:
                if player_['profileId'] == int(self.player['relicId']) :
                    victory = player_['won']
                    alias = player_['name']
                embed.add_field(name="{}#{} [{}] as {}".format( player_['name'],player_['profileId'], player_["rating"], player_["civName"]), value="")
        embed.description = "{}'s team {} this game".format(alias, 'won' if victory else 'lost')
        await interaction.response.edit_message(embed=embed)

class FAQMenu(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="FAQ", style=discord.ButtonStyle.blurple)
    async def FAQBox(self, interaction, button):
        await interaction.response.send_message("```1. For relic id, don't use aoe2insights. Use aoe2recs or aoe2companion instead.\n2. To find your steam id, look under Account Details on your steam page. It's a long long integer.```")

def displayStatsShort(discordId):
        player = {}
        res = cr.execute('select * from d2a where discordid={};'.format(discordId)).fetchall()
        try: 
            player['relicId'] = res[0][1]
        except (KeyError,IndexError) as exc:
            embed.description = "Invalid ID?"
            embed.add_field(name="Set your AoE profile", value="*-steamid <your steam id>* or *-relicid <link to your aoe2recs or aoe2companion profile>*", inline=False)
            return embed
        embed = discord.Embed(title="AoE2 Profile")
        jdata = requests.get(apis_.aoe2companionProfile(player['relicId'])).json()
        if 'profileId' not in jdata:
            embed.description = "Invalid ID?"
            embed.add_field(name="Set your AoE profile", value="*-steamid <your steam id>* or *-relicid <link to your aoe2recs or aoe2companion profile>*", inline=False)
            return embed
        embed.title = jdata['name']
        embed.colour = discord.Colour.random()
        for ldrbrd in jdata['leaderboards']:
            if ldrbrd['leaderboardName'] == '1v1 Random Map':
                embed.add_field(value="{}-{}".format(str(ldrbrd['rating']),str(ldrbrd['maxRating'])), name=ldrbrd['leaderboardName'],inline=True)
        embed.add_field(name="Add or Change", value="Type -steamid <your steam id> or -relicid <your aoe2 profile id>", inline=False)
        return embed

class StatusCode():
    def report(self):
        if self.code == -1:
            return "Invalid"
        elif self.code == 0:
            return "No effect"
        else:
            return self.message
        return ""

def registerId( authorId, steamId=-1, relicId =-1, guildID=""):
    status = StatusCode()
    r = {}
    if steamId != -1:
        r = requests.get(apis_.relicLinkPersonalStatsSteam(steamId)).json()
    elif relicId != -1:
        r = requests.get(apis_.relicLinkPersonalStatsRelic(relicId)).json()
    alias = ""
    try:
        relicId = str(r['statGroups'][0]['members'][0]['profile_id'])
        alias = r['statGroups'][0]['members'][0]['alias']
        #steamId = re.compile('[0-9]+').findall(r['statGroups'][0]['members'][0]['name'])[0]
    except KeyError as exc:
        status.code = -1
        return status

    cr.execute('insert into d2a values( {} , {} ) on conflict(discordid) do update set aoe2id={};'.format(int(authorId), int(relicId), int(relicId)))
    sqlc.commit()
    
    status.code = 1
    status.message = "Profile found : " + alias
    return status

def regexGetId(string):
    return re.compile('[0-9][0-9][0-9][0-9][0-9]+').findall(string)[0]

def isCommand(message):
    return message.content.startswith("-steamid") or message.content.startswith("-stats") or message.content.startswith("-relicid")

async def respond(message):
    if message.content.startswith('!steamid') or message.content.startswith("-steamid"):
        status = StatusCode()
        try:
            steamId= regexGetId(message.content)
            if message.mentions:
                status = registerId( message.mentions[0].id, steamId =steamId,  guildID = str(message.guild.id) )
            else:
                status = registerId( message.author.id, steamId =steamId, guildID = str(message.guild.id) ) 
        except IndexError as exc:
            status.code = -1
        if status.code == -1:
            await message.channel.send('Invalid', view=FAQMenu())
            return
        await message.channel.send(status.report())

    if message.content.startswith('!relicid') or message.content.startswith("-relicid"):
        status = StatusCode()
        try:
            relicId= regexGetId(message.content)
            if message.mentions:
                status = registerId( message.mentions[0].id, relicId=relicId, guildID = str(message.guild.id) )
            else:
                status = registerId( message.author.id, relicId=relicId, guildID = str(message.guild.id) )
        except IndexError as exc:
            status.code = -1
        if status.code == -1:
            await message.channel.send('Invalid', view=FAQMenu())
            return
        await message.channel.send(status.report())

    if message.content.startswith('!stats add') or message.content.startswith("-stats add"):
        relicId = regexGetId(message.content)
        if not  relicId or not message.mentions:
            return
        status = registerId( message.mentions[0].id, relicId =relicId)
        await message.channel.send(status.report())
        return

    if message.content.startswith('!stats') or message.content.startswith("-stats"):
        res  = cr.execute('select * from d2a where discordid={};'.format(message.author.id)).fetchall()
        if len(res) == 0:
            await message.channel.send('Id not set. See Stats under -help')
        if len(message.mentions)>0:
            await message.channel.send(view=StatsMenu(message.mentions[0].id), embed=displayStatsShort(message.mentions[0].id))
        else: 
            await message.channel.send(view=StatsMenu(message.author.id), embed=displayStatsShort(message.author.id))

