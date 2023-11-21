import discord
import recAnalysis
from random import randint
import datetime
import traceback
import os
from pymongo import MongoClient
from discord.ext import tasks
from discord import Colour
from dotenv import load_dotenv
import time
import re
load_dotenv()

dbclient = MongoClient(os.getenv('LOCALMONGOURI'), int(os.getenv('LOCALMONGOPORT')))
ella = dbclient.aoe2bot.ella
cello = dbclient.aoe2bot.cello


def updateWinners(quickId, aoe2rec):
    winners = recAnalysis.getWinners(aoe2rec)
    for w in winners:
        cello.update_one({'quickId':quickId}, {'$push': {'winner': w}})
    return

def isRegistered(discordId):
    return ella.find_one({'discordId':discordId, 'relicId':{'$exists':True}})

def isAuthorized(author):
    return str(author.top_role) == 'admin' or str(author.top_role)=='admins' or str(author.top_role)=='tourneyadmin' or str(author.top_role)=='gameAdmins'

def isCommunityGame(quickId):
    return cello.find_one({'quickId':quickId})

def removeAllClosedGames(guildId):
    cello.delete_many({'guildId':guildId,'isOpen':False})
    return

def ListOfGames(guildId):
    embed = discord.Embed(title="List of open and closed community games", description="Type **!community <ID>** to read/join/close any community game\n Example: **!community 375**\nAdmins can archive all closed games via **!community autoremove**")
    listOfGames = cello.find({'guildId':guildId})
    for i in listOfGames:
        try:
            openorclosed = "Open" if i['isOpen'] else "Closed"
            embed.add_field(name=f"{i['gName']} created by {i['creatorName']}, ({openorclosed})", value=f"**!community {i['quickId']}**", inline=False)
        except Exception as exc:
            pass
    return embed

def ListOfOpenGames(guildId):
    embed = discord.Embed(title="List of open community games", description="Type **!community <ID>** to read/join/close any community game\n Example: **!community 375**\n")
    listOfGames = cello.find({'guildId':guildId})
    threeDaysAgo = datetime.date.today() - datetime.timedelta(days=3)
    for i in listOfGames:
        if i['isOpen'] and datetime.date.fromtimestamp(i['createdAt']) > threeDaysAgo:
            embed.add_field(name=f"{i['gName']} created by {i['creatorName']} ({len(i['players'])} players joined)", value=f"**!community {i['quickId']}**", inline=False)
        else:
            cello.update_one({'quickId' : i['quickId'] }, { '$set': {'isOpen':False} })
    return embed

def commieGameContextEmbed(quickId):
    embed=discord.Embed(description="desc")
    cg = cello.find_one({'quickId':int(quickId)})
    if not cg:
        return embed
    embed.title = f"Community game : {cg['gName']}"
    embed.description = cg['gDesc']
    embed.add_field(name="Creator", value=cg['creatorName'], inline=True)
    embed.add_field(name="Created on", value=str(datetime.date.fromtimestamp(float(cg['createdAt']))), inline=True)
    embed.add_field(name="Open?", value=str(cg['isOpen']), inline=False)
    embed.add_field(name="Players", value=str(len(cg['players'])), inline=False)
    serialnumber = 1
    for p in cg['players']:
        pl = ella.find_one({'discordId':p})
        embed.add_field(name=f"{serialnumber}. {pl['name']}", value="", inline=False)
        serialnumber += 1
    embed.add_field(name="Winners", value=str(len(cg['winner'])), inline=False)
    serialnumber = 1
    for p in cg['winner']:
        pl = ella.find_one({'discordId':p})
        embed.add_field(name=f"{serialnumber}. {pl['name']}", value="", inline=False)
        serialnumber += 1
    return embed

def resetAll(guildId):
    cello.delete_many({'guildId':guildId})

class CommieDescModal(discord.ui.Modal, title='New Community Game'):
    name = discord.ui.TextInput(label="Name", placeholder="Community name goes here...", required=True, max_length=32, min_length=8)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.long, placeholder="Description goes here...", required=False)

    def __init__(self, view):
        super().__init__()
        assert view is not None
        self.view=view

    async def on_submit(self, interaction):
        self.view.setNameDesc(self.name.value, self.description.value)
        if len(self.name.value) > 7 :
            quickId = randint(100,999)
            cello.update_one({'quickId' : quickId}, {'$set': {'creatorId':interaction.user.id, 'guildId':self.view.guildId, 'creatorName':interaction.user.display_name,'gName':self.name.value, 'gDesc':self.description.value, 'createdAt': time.time(), 'isOpen':True, 'players':[], 'winner':[]}}, upsert=True)
            embed = discord.Embed(title=f"New Community Game: {self.name.value}")
            embed.description =str(self.description.value)
            embed.add_field(name='Creator', value=interaction.user.display_name)
            embed.add_field(name='ID', value=quickId)
            embed.add_field(name='Join', value=f"**!community {quickId}**")
            embed.add_field(name='Note', value=f"Community games are kept open for three days since creation.", inline=False)
            await interaction.response.send_message(embed=embed)

    async def on_error(self, interaction, error) -> None:
        await interaction.response.defer()
        traceback.print_exception(type(error), error, error.__traceback__)

class getAllOpenGamesButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="List Open games", style=discord.ButtonStyle.success)

    async def callback(self, interaction):
        assert self.view is not None
        await interaction.response.send_message(embed=ListOfOpenGames(self.view.guildId))

class getAllGamesButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="List All games", style=discord.ButtonStyle.grey)

    async def callback(self, interaction):
        assert self.view is not None
        await interaction.response.send_message(embed=ListOfGames(self.view.guildId))

class CreateCommunityGameButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Create new community game", style=discord.ButtonStyle.success, row=1)

    async def callback(self, interaction):
        assert self.view is not None
        await interaction.response.send_modal(CommieDescModal(self.view))

class LeaveCommunityGameButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Leave Game", style=discord.ButtonStyle.blurple, row=4)

    async def callback(self, interaction):
        assert self.view is not None
        cello.update_one({'quickId': self.view.quickId}, { '$pull' : {'players': interaction.user.id } } )
        await interaction.response.send_message(f"{interaction.user.display_name} has left community game")
        return

class PingAllPlayersButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Ping All", style=discord.ButtonStyle.blurple, row=3)

    async def callback(self, interaction):
        assert self.view is not None
        cg = cello.find_one({'quickId':self.view.quickId})
        await interaction.response.send_message(f"!ping "+str(cg['players']))
        return

class SetWinnersButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Who won?", style=discord.ButtonStyle.blurple, row=3)

    async def callback(self, interaction):
        assert self.view is not None
        await interaction.response.send_message(f"To update data to show winners, type **!community {self.view.quickId}** and attach recording file**.\n Only original creator or admins can do this for each community game")
        return


class JoinCommunityGameButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Join Game", style=discord.ButtonStyle.blurple, row=4)

    async def callback(self, interaction):
        assert self.view is not None
        cg = cello.find_one({'quickId': self.view.quickId})
        if not isRegistered(interaction.user.id):
            await interaction.response.send_message(f"{interaction.user.display_name} is not registered. See Stats under !help")
            return
        if not cg['isOpen']:
            await interaction.response.send_message(f"Replying to {interaction.user.display_name}. Game is closed.")
            return
        if interaction.user.id in cg['players']:
            await interaction.response.send_message(f"{interaction.user.display_name} is already a part of this community game.")
            return
        cello.update_one({'quickId': self.view.quickId}, { '$push' : {'players': interaction.user.id } } )
        await interaction.response.send_message(f"{interaction.user.display_name} has joined {cg['gName']} community game")
        return


class DeleteCommunityGameButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Close game", style=discord.ButtonStyle.red, row=4)

    async def callback(self, interaction):
        assert self.view is not None
        if isAuthorized(interaction.user):
            cello.update_one({'quickId':self.view.quickId}, {'$set':{'isOpen':False}}, upsert=True)
            await interaction.response.send_message(f"Community game {self.view.quickId} closed via admin privilege")
            return
        else:
            if not cello.find_one({'quickId':self.view.quickId,'creatorId':interaction.user.id}) :
                await interaction.response.send_message('Not authorized. Only admins, gameAdmins and original creator of the game is allowed to close it')
                return
            cello.update_one({'quickId':self.view.quickId}, {'$set':{'isOpen':False}})
            await interaction.response.send_message(f"Community game {self.view.quickId} closed via creator privilege")
            return

class RefreshButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Refresh", style=discord.ButtonStyle.grey)

    async def callback(self, interaction):
        assert self.view is not None
        await interaction.response.send_message(view=CommunityGameContextMenu(self.view.quickId), embed=commieGameContextEmbed(self.view.quickId))

class CommunityGameContextMenu(discord.ui.View):
    def __init__(self, quickId):
        super().__init__(timeout=1000)
        self.quickId = quickId
        self.add_item(JoinCommunityGameButton())
        self.add_item(LeaveCommunityGameButton())
        self.add_item(PingAllPlayersButton())
        self.add_item(SetWinnersButton())
        self.add_item(RefreshButton())
        self.add_item(DeleteCommunityGameButton())


class CommunityGameMenu(discord.ui.View):
    creatorId=-1
    guildId=-1
    gameName=""
    gameDesc=""

    def __init__(self, creatorId, guildId, creatorName, guildName):
        super().__init__()
        self.creatorId=creatorId
        self.guildId=guildId
        self.creatorName= creatorName
        self.guildName= guildName
        self.add_item(CreateCommunityGameButton())
        self.add_item(getAllOpenGamesButton())
        self.add_item(getAllGamesButton())

    def setNameDesc(self, name, desc):
        self.gameName=name
        self.gameDesc=desc

