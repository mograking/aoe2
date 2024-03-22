import json
import re
import requests
import apis_
import discord


def isCommand(message):
    return message.content.startswith('-search')

async def respond(message):
    aliasPartial = ' '.join(message.content.split(' ')[1:])
    resultText = ''
    r = []
    try : 
        r= requests.get(apis_.aoe2companionSearchNew(aliasPartial)).json()
    except json.decoder.JSONDecodeError as exc:
        print(exc)
        return
    try:
        count = 5
        for x in r['profiles']:
            count -= 1
            resultText += '# {} \n'.format(x['name'])
            resultText += ' - Id:{} Country:{} Games:{} Clan:{} \n'.format(x['profileId'],x['country'],x['games'],x['clan'])
            try: 
                v = requests.get(apis_.aoe2companionProfile(x['profileId'])).json()
                _1v1 = 0
                _unranked = 0
                _team = 0
                for w in v['leaderboards']:
                    if w['leaderboardId']=='rm_1v1':
                        _1v1=w['rating']
                    if w['leaderboardId']=='rm_team':
                        _team=w['rating']
                    if w['leaderboardId']=='unranked':
                        _unranked=w['rating']
                resultText += ' - 1v1 {} | Team {} | Unranked {} \n'.format( _1v1, _team, _unranked)
            except Exception as exc:
                print(exc)
                pass
            if not count:
                break
    except IndexError as exc:
        print(exc)
        return
    try:
        await message.channel.send("```md\n{}```".format(resultText))
    except Exception as exc:
        print(exc)
        pass




async def respond_old(message):
    aliasPartial = ' '.join(message.content.split(' ')[1:])
    resultText =''
    r = []
    try:
        r= requests.get(apis_.aoe2companionSearchrm1v1(aliasPartial)).json()
    except json.decoder.JSONDecodeError as exc:
        pass
    try:
        count = 5
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
