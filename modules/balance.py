import json
import math
import re
import requests
import apis_
import sqlite3
import discord

from dotenv import load_dotenv
load_dotenv()

sqlc =sqlite3.connect('discordToAoe.db') 
cr = sqlc.cursor()

def sumSplit(left,right=[],difference=0):
    sumLeft,sumRight = sum([x[1] for x in left]),sum([x[1] for x in right])

    # stop recursion if left is smaller than right
    if sumLeft<sumRight or len(left)<len(right): return

    # return a solution if sums match the tolerance target
    if sumLeft-sumRight == difference:
        return left, right, difference

    # recurse, brutally attempting to move each item to the right
    for i,value in enumerate(left):
        solution = sumSplit(left[:i]+left[i+1:],right+[value], difference)
        if solution: return solution

    if right or difference > 0: return
    # allow for imperfect split (i.e. larger difference) ...
    for targetDiff in range(1, sumLeft-min([x[1] for x in left])+1):
        solution = sumSplit(left, right, targetDiff)
        if solution: return solution


def getBalancedTeams(name_elo):
    team_1 = []
    team_2 = []

    return sumSplit(name_elo)

    return ( team_1, team_2 )


def norm_1(rating) : 
    return math.ceil( math.exp(rating/1000)*1000 )

def norm_2(rating):
    return math.ceil( math.exp( max(rating-500, 500)/1000 )*1000)

def norm_3(rating):
    return math.ceil( math.exp( (rating-1000)/1000 )*1000)


def normalize(rating):
    return norm_3(rating)

def isCommand(message):
    return message.content.startswith('-balance')

async def respond(message):
    if len(message.content.split(' ')) == 2 and message.content.split(' ')[1] == 'help':
        resultText = '''Normalized rating is a function of rating designed to treat higher ELOs as exponentially higher to make balancing fair'''
        try:
            await message.channel.send("```md\n{}```".format(resultText))
        except Exception as exc:
            pass
        finally:
            return

    player_list = message.author.voice.channel.members
    player_to_elo = {} 
    name_elo = [] 
    resultText = ''
    errorText = []
    for x in player_list:
        res = cr.execute('select * from d2a where discordid={};'.format(x.id)).fetchall()
        try: 
            relicId = res[0][1]
        except IndexError as exc:
            errorText += [x.display_name]
            continue

        jdata = requests.get(apis_.relicLinkPersonalStatsRelic(relicId)).json()
        rating = 0
        try:
            for y in jdata['leaderboardStats']:
                if y['leaderboard_id']==3:
                    rating=y['rating']
                    break
        except IndexError as exc:
            errorText += [x.display_name]
            continue
        except KeyError as exc:
            errorText += [x.display_name]
            continue
        name_elo += [ (x.display_name, normalize(rating), rating ) ]
    team_1, team_2, difference = getBalancedTeams(name_elo)
    team_1 = '\n'.join( [ '- {} rating={} normalized={}'.format(x[0],x[2],x[1]) for x in team_1 ] )
    team_2 = '\n'.join( [ '- {} rating={} normalized={}'.format(x[0],x[2],x[1]) for x in team_2 ] )
    resultText = '''# Team 1\n\
{}\n\
# Team 2\n\
{}\n\
# Difference \n\
{}\
'''.format(team_1, team_2, difference)

    resultText = resultText.replace('_',' ')
    if len(errorText) :
        errorText = ', '.join(errorText)
        errorText = errorText.replace('_', ' ')
    resultText += '\n# No ID\n'+ str(errorText)+'\n'
    resultText += '\n# Help\n- Type "-balance help" for help text.'
    try:
        await message.channel.send("```md\n{}```".format(resultText))
    except Exception as exc:
        pass
