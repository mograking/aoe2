from pymongo import MongoClient
import urllib
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import requests
import os
load_dotenv()

client = MongoClient()

DBUSR = os.getenv('DBUSR')
DBPWD = os.getenv('DBPWD')
uri ='mongodb+srv://'+DBUSR+':'+urllib.parse.quote(DBPWD)+'@cluster0.1ui1r.mongodb.net/?retryWrites=true&w=majority'

#col.insert_one({pid : '111', al : 'Test Dummy'})
#col.find({pid:'111'}).limit(1)[0][al]

client = MongoClient(uri, server_api=ServerApi('1'))

client.admin.command('ping')

col =  client.profiles.aoe2

PID = 'profile_id'
AL = 'alias'
EL = 'elo'
GU = 'guild'
RAV = 'runningElo'

def isIDValid(profile_id):
    r = requests.get('https://aoe-api.reliclink.com/community/leaderboard/GetPersonalStat?title=age2&profile_ids=["'+str(profile_id)+'"]').json()
    return r['result']['code'] == 0

def addID(profile_id, guild_id):
    r = requests.get('https://aoe-api.reliclink.com/community/leaderboard/GetPersonalStat?title=age2&profile_ids=["'+str(profile_id)+'"]').json()
    if r['result']['message']=='SUCCESS':
        alias_ = r['statGroups'][0]['members'][0]['alias']
        elo_ = -1
        for x in r['leaderboardStats']:
            if x['leaderboard_id'] == 3:
                elo_ = x['rating']
        col.insert_one({PID : str(profile_id), AL :alias_, EL : elo_, GU : str(guild_id) })
        return alias_
    else:
        return False

def updateELOs(list_of_profile_ids):
    for y in list_of_profile_ids:
        r = requests.get('https://aoe-api.reliclink.com/community/leaderboard/GetPersonalStat?title=age2&profile_ids=["'+str(y)+'"]').json()
        if r['result']['message']=='SUCCESS':
            for x in r['leaderboardStats']:
                if x['leaderboard_id'] == 3:
                    elo_ = x['rating']
                    col.update_one({PID:y}, { '$set': {EL: elo_ }})

def isIDpresent(profile_id, guild_id):
    return col.find_one({PID:profile_id, GU:guild_id}) != None
    
def updateInfo(profile_id, data):
    col.update_one({PID:profile_id}, { '$set' : data} ) 

def getInfo(profile_id):
    return col.find_one({PID: profile_id}) 

def updateELOForGuild(guild_id):
    updateELOs( [ x[PID] for x in col.find({GU:guild_id}) ] )

def updateAllELOs():
    updateELOs( [ x[PID] for x in col.find({}) ] )

def getELOforGuild(guild_id):
    return [ (x[AL], x[EL], -1 if RAV not in x else x[RAV]) for x in col.find({GU: guild_id}).sort(EL) ]

def updateRunningAvg(profile_id, running_avg):
    col.update_many({PID:profile_id}, { '$set': {RAV: int(running_avg) }})

def getListOfAllIds():
    return [ x[PID] for x in col.find({}) ]

if __name__=='__main__':
    updateAllELOs()
    
