
import re
import requests
import json

import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv()

dbclient = MongoClient(os.getenv('LOCALMONGOURI'), int(os.getenv('LOCALMONGOPORT')))
ella = dbclient.aoe2bot.ella

def getName(relicId):
    try:
        return ella.find_one({'relicId':relicId})['name']
    except KeyError as exc:
        return ""

def isRelicIdValid(profile_id):
    return 'error' not in requests.get('https://data.aoe2companion.com/api/profiles/'+profile_id+'?profile_id='+profile_id+'&page=1').json()

class StatusCode():
    def report(self):
        if self.code == -1:
            return "Invalid"
        elif self.code == 0:
            return "No effect"
        else:
            return self.message
        return ""

def addIdToTracking(relicId, discordId):
    relicId = str(relicId)
    status = StatusCode()
    if not isRelicIdValid(relicId):
        status.code = -1
    if ella.find_one({'relicId': relicId, 'discordId' : discordId } ) :
        status.code = 0
    ella.update_one({'relicId' : relicId} , { '$set': {'discordId' : discordId, 'subscribed': 'true'}} , upsert=True)
    status.code = 1
    status.message = 'AoE2 profile found! Added to subscription list ' + getName(relicId)
    return status

def removeTracking(discordId):
    status = StatusCode()
    if not ella.find_one({'discordId':discordId}):
        status.code = -1
    if ella.find_one({'discordId':discordId, 'subscribed':'false'}):
        status.code = 0
    ella.update_many({'discordId' : discordId} , { '$set' : {'subscribed' : 'false' } } )
    status.code = 1
    status.message = 'Removed from subscription list' 
    return status

def regexGetId(string):
    return re.compile('[0-9][0-9][0-9][0-9][0-9]+').findall(string)[0]

def isCommand(message):
    return message.content.startswith('!sub') or message.content.startswith('-sub') or message.content.startswith('-unsub') or message.content.startswith('!unsub')

async def respond(message):
    if  message.content.startswith('!sub') or message.content.startswith("-sub"):
        relicId = regexGetId(message.content)
        if relicId == "":
            await message.channel.send("Try !sub <relic id> to get updates on your ongoing matches")
            return
        status =  addIdToTracking(relicId, message.author.id)
        await message.channel.send(status.report() + "\n Use !sub <relicid> to receive information on your ongoing matches")
        return

    if  message.content.startswith('!unsub') or message.content.startswith("-unsub"):
        status = removeTracking(message.author.id)
        await message.channel.send(status.report())
        return
