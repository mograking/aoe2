import discord
import math
import sqlite3
import json

sqlc =sqlite3.connect('discordToCountScore.db') 
cr = sqlc.cursor()

async def apply_score(message):
    user_id = message.author.id
    display_name = message.author.display_name
    count_value = 0
    try:
        count_value = eval(message.content)
    except (NameError, KeyError, IndexError, SyntaxError, ArithmeticError, AttributeError, ImportError, TypeError) as exc:
        return (display_name, 'Error: Unable to grok value from message.', 0)
    result = cr.execute('select * from d2c where uid={};'.format(user_id)).fetchall()
    if len(result) == 0:
        # create user 
        cr.execute('insert into d2c values ( {} , {} );'.format(user_id, count_value))
        sqlc.commit()
        return (display_name, 'Scored!', count_value)
    current_score = int(result[0][1])
    cr.execute('update d2c set score={} where uid={};'.format(current_score+count_value, user_id))
    sqlc.commit()
    return ( display_name, 'Scored!', current_score+count_value )

def isCommand(message):
    return message.content.startswith('-score')

async def respond(message):
    result = cr.execute('select * from ( select uid, score, rank() over ( order by score desc ) scorerank from d2c ) where uid={};'.format(message.author.id) ).fetchall()
    result2 = cr.execute('select count(*) from d2c;').fetchall()
    if len(result)> 0 and len(result2) > 0:
        await message.channel.send('Your total score is {} and rank is {} among {} members.'.format(result[0][1], result[0][2], result2[0][0]))
    else: 
        await message.channel.send('No score found.')









