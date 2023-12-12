import re
import os
from dotenv import load_dotenv
import discord

load_dotenv()


def customLobbyMenu(author, gameId):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Join "+str(author)+"\'s game", url="http://"+str(os.getenv('SERVERHTTP'))+"?gameId="+str(gameId)+"&spectate=0"))
    view.add_item(discord.ui.Button(label="Spectate", url="http://"+str(os.getenv('SERVERHTTP'))+"?gameId="+str(gameId)+"&spectate=1"))
    return view

def isCommand(message):
    aoe2de_pattern = re.compile('''aoe2de:\/\/0\/[0-9]+''')
    return aoe2de_pattern.findall(message.content)

async def respond(message):
        try:
            matchId = re.compile('[0-9][0-9][0-9][0-9]+').findall(message.content)[0]
        except IndexError as exc:
            return
        await message.channel.send(view = customLobbyMenu(message.author.name, matchId))
        return
