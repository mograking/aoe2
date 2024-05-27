import modules.helpUI as help
#import modules.override as override
import modules.balance as balance
import modules.lobbyLinks as links
import modules.search as search
import modules.stats as stats
import modules.countscore as countscore
import modules.civilizations as civs

import modules.bracket as bracket
import os
import discord
from discord.ext import tasks
from dotenv import load_dotenv
load_dotenv()

client = discord.Client(intents=discord.Intents.all())

COUNT_BOT_ID=510016054391734273 
COUNT_CHANNEL_ID=1230924192640405646 
COUNT_VERIFIED_EMOJI='✅'

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    print( str(len(client.guilds)) + ' number of active servers ')

@client.event
async def on_raw_reaction_add(payload):
    if payload.channel_id == COUNT_CHANNEL_ID and payload.user_id == COUNT_BOT_ID and payload.emoji.name == COUNT_VERIFIED_EMOJI:
        message = await (await client.fetch_channel(COUNT_CHANNEL_ID)).fetch_message(payload.message_id)
        response = await countscore.apply_score(message)
        await message.channel.send('{} {} {}'.format(response[0],response[1],response[2]))

@client.event
async def on_message(message):
    if len(message.content) > 250 or message.author.bot:
        return

    if message.content == '-ping':
        await message.channel.send('pong-')

    if stats.isCommand(message):
        await stats.respond(message)

    if countscore.isCommand(message):
        await countscore.respond(message)

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
