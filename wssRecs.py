import websocket
import logging
import aoe2database
import json
import base64
import _thread
import time
import rel
from statistics import mean

def extractRunningAverage(k, limit=20):
    c = str(k['data']['player']['id'])
    print(c)
    suma = 0
    for x in k['data']['ratings']:
        if x['name'] == '1v1 Random Map':
            for i in range(-1, -limit-1, -1):
                suma += x['data'][i][c] 
            break
    b = suma/limit #mean
    return b

def extractHighestElo(k):
    for x in k['data']['ladders']:
        if x['name'] == '1v1 Random Map':
            return x['highest']
    return -1

def on_message(ws, message):
    jdata = json.loads(message)
    if jdata['cls']==13:
        profile_id = jdata['data']['player']['id']
        running_average = extractRunningAverage(jdata)
        highest_elo = extractHighestElo(jdata)
        aoe2database.updateGeneralMany( { aoe2database.PID : str(profile_id) } , { aoe2database.RAV : int(running_average) , aoe2database.HEL : int(highest_elo) } )

def on_error(ws, error):
    pass

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")

def OpenWebSocket(profile_ids):
    aoe2recsAPI = "wss://aoe2recs.com/dashboard/api/"
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(aoe2recsAPI,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    for y in profile_ids:
        msg = '{"profile_id":'+y+'}'
        ws.send(msg)
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()

logging.basicConfig(filename='wssRecs.log', encoding='utf-8', level=logging.INFO)

if __name__=='__main__':
    logging.debug('updating running avg')
    ws = OpenWebSocket(aoe2database.getListOfAllIds())

