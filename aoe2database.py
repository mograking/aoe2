from pymongo import MongoClient
import logging
import urllib
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import requests
import os
load_dotenv()

client = MongoClient()

DBUSR = os.getenv('DBUSR')
DBPWD = os.getenv('DBPWD')
DBURI = os.getenv('DBURI')

uri ='mongodb+srv://'+DBUSR+':'+urllib.parse.quote(DBPWD)+'@'+DBURI+'/?retryWrites=true&w=majority'

client = MongoClient(uri, server_api=ServerApi('1'))

client.admin.command('ping')

col =  client.profiles.aoe2
trackCol = client.profiles.tracked
ONcol = client.profiles.ongoingmatches

# Document keys

PID = 'profile_id'
AL = 'alias'
EL = 'elo'
GU = 'guild'
RAV = 'runningElo'
HEL = 'highestElo'
TEL = 'teamElo'
TRK = 'tracked'
AID = 'author_id'
MID = 'match_id'
PYRS = 'players'
MP = 'map'


def addMatchON(profile_id, match_id, players, map_):
    ONcol.insert_one({PID: str(profile_id), MID : match_id, PYRS: players, MP : map_ } )

def removeMatchON(query):
    ONcol.delete_one(query)

def dumpON():
    ONcol.delete_many({})

def getAuthor(profile_id):
    return trackCol.find_one({PID:profile_id})

def getAllOngoing():
    return ONcol.find({})

def getAllTracked():
    return [ x[PID] for x in trackCol.find({}) ] 

def isTracked(profile_id):
    X = trackCol.find_one({PID:str(profile_id)})
    if X:
        return X[AID]
    return -1

def addToTracking(profile_id, author_id):
    if trackCol.find_one({PID: str(profile_id), AID: author_id}) != None:
        return 2
    if not isIDValid(profile_id):
        return 3
    trackCol.insert_one({PID:str(profile_id), AID: author_id})
    return 1

def isIDValid(profile_id):
    r = requests.get('https://aoe-api.reliclink.com/community/leaderboard/GetPersonalStat?title=age2&profile_ids=["'+str(profile_id)+'"]').json()
    return r['result']['code'] == 0

def addID(profile_id, guild_id):
    r = requests.get('https://aoe-api.reliclink.com/community/leaderboard/GetPersonalStat?title=age2&profile_ids=["'+str(profile_id)+'"]').json()
    if r['result']['message']=='SUCCESS':
        alias_ = r['statGroups'][0]['members'][0]['alias']
        elo_ = -1
        helo_ = -1
        telo_ = -1
        for x in r['leaderboardStats']:
            if x['leaderboard_id'] == 3:
                    elo_ = x['rating']
                    helo_ = x['highestrating']
            if x['leaderboard_id']==4:
                    telo_ = x['rating']
        col.insert_one({PID : str(profile_id), AL :alias_, EL : elo_, TEL: telo_, HEL: helo_,  GU : str(guild_id),  })
        return alias_
    else:
        return False

def getELOquick(profile_id):
    elo_ = -1
    r = requests.get('https://aoe-api.reliclink.com/community/leaderboard/GetPersonalStat?title=age2&profile_ids=["'+str(profile_id)+'"]').json()
    if r['result']['message']=='SUCCESS':
        for x in r['leaderboardStats']:
            if x['leaderboard_id'] == 3:
                elo_ = x['rating']
    return elo_

def updateELOs(list_of_profile_ids):
    for y in list_of_profile_ids:
        r = requests.get('https://aoe-api.reliclink.com/community/leaderboard/GetPersonalStat?title=age2&profile_ids=["'+str(y)+'"]').json()
        if r['result']['message']=='SUCCESS':
            for x in r['leaderboardStats']:
                if x['leaderboard_id'] == 3:
                    elo_ = x['rating']
                    helo_ = x['highestrating']
                    col.update_one({PID:y}, { '$set': {EL: elo_, HEL:helo_ }})
                if x['leaderboard_id']==4:
                    telo_ = x['rating']
                    col.update_one({PID:y}, { '$set': {TEL: telo_}})

def isIDpresent(profile_id, guild_id):
    return col.find_one({PID:profile_id, GU:guild_id}) != None
    
def updateAllELOs():
    updateELOs( [ x[PID] for x in col.find({}) ] )

def getELOforGuild(guild_id):
    return [ (x[AL], x[EL], -1 if RAV not in x else x[RAV], -1 if HEL not in x else x[HEL], -1 if TEL not in x else x[TEL] ) for x in col.find({GU: guild_id}).sort(EL,-1) ]

def updateGeneralMany(selection, updating):
    col.update_many(selection, { '$set' : updating } )

def getListOfAllIds():
    return [ x[PID] for x in col.find({}) ]

logging.basicConfig(filename='aoe2database.log', encoding='utf-8', level=logging.INFO)

if __name__=='__main__':
    logging.debug('Updating ELOs')
    updateAllELOs()
    
