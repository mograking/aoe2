import modules.helpUI as help
import modules.taunts as taunts
import modules.bracket as bracket
import modules.lobbyLinks as links
import modules.search as search
import modules.stats as stats

import os
import discord
from dotenv import load_dotenv
load_dotenv()

client = discord.Client(intents=discord.Intents.all())

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

    if bracket.isCommand(message):
        await bracket.respond(message)

    if stats.isCommand(message):
        await stats.respond(message)

    if links.isCommand(message):
        await links.respond(message)

    if help.isCommand(message):
        await help.respond(message)

    if search.isCommand(message):
        await search.respond(message)

client.run(os.getenv('DISCORD_TOKEN'))
