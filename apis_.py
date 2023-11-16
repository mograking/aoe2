
def relicLinkPersonalStatsSteam(steamId):
    return "https://aoe-api.reliclink.com/community/leaderboard/GetPersonalStat?title=age2&profile_names=[\"/steam/"+str(steamId)+"\"]"

def relicLinkPersonalStatsRelic(relicId):
    return "https://aoe-api.reliclink.com/community/leaderboard/GetPersonalStat?title=age2&profile_ids=[\""+str(relicId)+"\"]"

def aoe2companionMatches(relicId):
    return 'https://data.aoe2companion.com/api/matches?profile_ids='+str(relicId)+'&search=&leaderboard_ids=&page=1'

def aoe2companionProfile(relicId):
    return 'https://data.aoe2companion.com/api/profiles/'+str(relicId)+'?profile_id='+str(relicId)+'&page=1'
