import requests
import datetime
import json

def getJSON(playerID):
    url = '''https://api.ageofempires.com/api/v2/AgeII/GetMPMatchList'''
    headers = {
        "Host": "api.ageofempires.com",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.ageofempires.com/",
        "Content-Length": "168",
        "Origin": "https://www.ageofempires.com",
        "Connection": "keep-alive",
        "Cookie": "MSCC=NR; _ga_V8LF07J0WF=GS1.1.1698308558.2.1.1698311239.60.0.0; _ga=GA1.1.2057243944.1698304769; _clck=1m6lcv7|2|fg6|0|1394; _gid=GA1.2.261773438.1698304770; _clsk=1tg4xqb|1698311172992|18|1|w.clarity.ms/collect",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-site",
        "TE": "trailers",
        "Content-Type": "application/json",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache" }
    data = '''{"gamertag":null,"playerNumber":0,"gameId":0,"game":"age2","profileId":'''+str(playerID) +''',"sortColumn":"dateTime","sortDirection":"DESC","page":1,"recordCount":10,"matchType":"3"}'''
    jdata = json.loads(data)
    r = requests.post(url, headers=headers,json=jdata)
    return r.json()

def dateFlag(date):
    r = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
    a_month_ago= datetime.datetime.today() - datetime.timedelta(days=30)
    return 1 if r > a_month_ago else 0 

def runCreditCheckBulk():
    file = open('CsvFiles/playerID.csv', 'r')
    outfile = open('hasPlayed10inlast30days.csv', 'w')
    outfile.write('playerID,hasPlayed10inlast30days\n')
    errorIDs = []
    for player in file.readlines()[1:]:
        player = str(int(player[:-1]))
        jd = getJSON(player)
        try:
            jdte = jd['matchList'][-1]['dateTime']
            outfile.write(player+','+str(dateFlag(jdte))+'\n')
        except IndexError as exc:
            outfile.write(player+',-1\n')
            print('Error at')
            print(player)
            print(jd)
            errorIDs += [player]
            pass
    outfile.close()
    return errorIDs

