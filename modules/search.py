import json
import re
import requests
import apis_
import discord


def isCommand(message):
    return message.content.startswith('-search')

async def respond(message):
    aliasPartial = ' '.join(message.content.split(' ')[1:])
    resultText =''
    r = []
    try:
        r= requests.get(apis_.aoe2companionSearchrm1v1(aliasPartial)).json()
    except json.decoder.JSONDecodeError as exc:
        pass
    try:
        count = 2
        for x in r['players']:
            count -= 1
            resultText += '\n {} {} {} #{}'.format(x['leaderboardId'], x['name'], x['rating'], x['profileId'])
            if not count:
                break
    except IndexError as exc:
        pass

    r = []
    try:
        r= requests.get(apis_.aoe2companionSearchrmteam(aliasPartial)).json()
    except json.decoder.JSONDecodeError as exc:
        pass
    try:
        count = 2
        for x in r['players']:
            count -= 1
            resultText += '\n {} {} {} #{}'.format(x['leaderboardId'], x['name'], x['rating'], x['profileId'])
            if not count:
                break
    except IndexError as exc:
        pass

    r = []
    try:
        r= requests.get(apis_.aoe2companionSearchunranked(aliasPartial)).json()
    except json.decoder.JSONDecodeError as exc:
        pass
    try:
        count = 2
        for x in r['players']:
            count -= 1
            resultText += '\n {} {} {} #{}'.format(x['leaderboardId'], x['name'], x['rating'], x['profileId'])
            if not count:
                break
    except IndexError as exc:
        pass
    try:
        await message.channel.send("```{}```".format(resultText))
    except Exception as exc:
        pass
