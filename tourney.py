import discord
import traceback
import os
from pymongo import MongoClient
from discord.ext import tasks
from discord import Colour
from dotenv import load_dotenv
import re
load_dotenv()

dbclient = MongoClient(os.getenv('LOCALMONGOURI'), int(os.getenv('LOCALMONGOPORT')))
ella = dbclient.aoe2bot.ella

def isAuthorized(author):
    return str(author.top_role) == 'admin' or str(author.top_role)=='admins' or str(author.top_role)=='tourneyadmin'

class TourneyDescModal(discord.ui.Modal, title='Name of the Tourney'):
    name = discord.ui.TextInput(label="Name", placeholder="Tourney name goes here...", required=True, max_length=32, min_length=8)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.long, placeholder="Tourney description goes here...", required=False)

    def __init__(self, view):
        super().__init__()
        assert view is not None
        self.view=view

    async def on_submit(self, interaction):
        if not isAuthorized(interaction.user):
            await interaction.response.send_message("Not authorized. Only admins and tourneyadmin roles can use tourney creator menu")
            return
        self.view.setNameDesc(self.name.value, self.description.value)
        await interaction.response.edit_message(view=self.view, embed=discord.Embed(title=f"New Tourney", description=f"**Name: {self.name.value}**\nDescription: {self.description.value}\n"))

    async def on_error(self, interaction, error) -> None:
        await interaction.response.defer()
        traceback.print_exception(type(error), error, error.__traceback__)

class SetTourneyDesc(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Set Tourney Desc", style=discord.ButtonStyle.success, row=1)

    async def callback(self, interaction):
        if not isAuthorized(interaction.user):
            await interaction.response.send_message("Not authorized. Only admins and tourneyadmin roles can use tourney creator menu")
            return
        assert self.view is not None
        await interaction.response.send_modal(TourneyDescModal(self.view))

class NumberOfBracketsInput(discord.ui.Select):
    def __init__(self):
        super().__init__(custom_id="nmbrk",placeholder="Select Nu of Brackets", min_values=1, max_values=1,  options=[discord.SelectOption(label=str(x),value=x) for x in range(1,5)], row=2)

    async def callback(self, interaction):
        if not isAuthorized(interaction.user):
            await interaction.response.send_message("Not authorized. Only admins and tourneyadmin roles can use tourney creator menu")
            return
        assert self.view is not None
        self.view.numberOfBrackets = self.values[0]
        await interaction.response.defer()

class InviteOnlyOption(discord.ui.Select):
    def __init__(self):
        super().__init__(custom_id="ioopt", placeholder="Open/Closed", min_values=1, max_values=1,  options= [discord.SelectOption(label="Invite Only",value=1),discord.SelectOption(label="Open",value=2)], row=3)

    async def callback(self, interaction):
        if not isAuthorized(interaction.user):
            await interaction.response.send_message("Not authorized. Only admins and tourneyadmin roles can use tourney creator menu")
            return
        assert self.view is not None
        self.view.inviteOnly= self.values[0]
        await interaction.response.defer()

class CreateButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Create",style=discord.ButtonStyle.success, row=4)

    async def callback(self,interaction):
        if not isAuthorized(interaction.user):
            await interaction.response.send_message("Not authorized. Only admins and tourneyadmin roles can use tourney creator menu")
            return
        assert self.view is not None
        if not self.view.tourneyName or not self.view.tourneyDesc:
            await interaction.response.send_message("Name or description not set")
            return

        if not self.view.numberOfBrackets:
            await interaction.response.send_message("Number of brackets not set")
            return

        if not self.view.inviteOnly:
            await interaction.response.send_message("Please select Open or Invite Only")
            return

        print(self.view.tourneyName)
        print(self.view.tourneyDesc)
        print(self.view.guildId)
        print(self.view.creatorId)
        print(self.view.inviteOnly)
        print(self.view.numberOfBrackets)

        for i in self.view.children:
            try:
                print(i.value)
            except Exception as exc:
                pass
            try:
                print(i.values)
            except Exception as exc:
                pass

class TourneyCreatorMenu(discord.ui.View):
    creatorId=-1
    guildId=-1
    tourneyName=""
    tourneyDesc=""
    tourneyBrackets=[]
    inviteOnly=False
    numberOfBrackets= 0

    def __init__(self, creatorId, guildId):
        super().__init__()
        self.creatorId=creatorId
        self.guildId=guildId
        self.add_item(SetTourneyDesc())
        self.add_item(NumberOfBracketsInput())
        self.add_item(InviteOnlyOption())
        self.add_item(CreateButton())

    def setNameDesc(self, name, desc):
        self.tourneyName=name
        self.tourneyDesc=desc

