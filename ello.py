import modules.helpUI as help
#import modules.override as override
import modules.balance as balance
import modules.lobbyLinks as links
import modules.search as search
import modules.stats as stats
import modules.civilizations as civs

import modules.bracket as bracket
import os
import discord
from discord.ext import tasks
from dotenv import load_dotenv
load_dotenv()

client = discord.Client(intents=discord.Intents.all())

lfgs = dict()
billboard = None

@tasks.loop(minutes=20)
async def refreshBillBoard():
    await lfg.refresh()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    for g in client.guilds:
        print(f"{g.id} = {g.name}")

@client.event
async def on_message(message):
    if len(message.content) > 250 or message.author.bot:
        return

    if message.content == '-ping':
        await message.channel.send('pong-')

    if stats.isCommand(message):
        await stats.respond(message)

    if bracket.isCommand(message):
        await bracket.respond(message)

    if links.isCommand(message):
        await links.respond(message)

    if help.isCommand(message):
        await help.respond(message)

    if search.isCommand(message):
        await search.respond(message)

    if civs.isCommand(message):
        await civs.respond(message)

    if balance.isCommand(message):
        await balance.respond(message)

client.run(os.getenv('DISCORD_TOKEN'))
