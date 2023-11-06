import aoe2database as aoe2db
from threading import Thread
import websocket
import json
import base64
import _thread
import time
import rel

def relevant(tset, players):
    l =[]
    for x in players:
        if str(x['profileId']) in tset:
            l += [x['profileId']]
    return l

def processMsg(jdata):
    tlist = aoe2db.getAllTracked()
    tset = set(tlist)
    ii = 0
    for x in jdata:
        ii += 1
        match_id = x['data']['matchId']
        if x['type'] == 'matchAdded':
            r = relevant(tset, x['data']['players'])
            if len(r):
                players = []
                for p in x['data']['players']:
                    players += [ [ p['name'] if 'name' in p else 'player', p['rating'] if 'rating' in p else -1 , p['profileId'] ] ]
                map_name = x['data']['mapName'] if 'mapName' in x['data'] else 'map'
                for rr in r :
                    aoe2db.addMatchON(rr, match_id, players, map_name)
        if x['type'] == 'matchRemoved':
            aoe2db.removeMatchON({'match_id': match_id} )

def on_message(ws, message):
    jdata = json.loads(message)
    Thread(target=processMsg, args=(jdata,)).start()

def on_error(ws, error):
    pass

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")

def restart():
    aoe2compAPI= "wss://socket.aoe2companion.com/listen?handler=ongoing-matches"
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(aoe2compAPI,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever( reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly

if __name__ == "__main__":
    aoe2compAPI= "wss://socket.aoe2companion.com/listen?handler=ongoing-matches"
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(aoe2compAPI,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    rel.dispatch()

