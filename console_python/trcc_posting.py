# |-----------------------------------------------------------------------------
# |            This source code is provided under the Apache 2.0 license      --
# |  and is provided AS IS with no warranty or guarantee of fit for purpose.  --
# |                See the project's LICENSE.md for details.                  --
# |           Copyright Thomson Reuters 2017. All rights reserved.            --
# |-----------------------------------------------------------------------------


#!/usr/bin/env python
""" Simple example of posting Market Price JSON data To TRCC via TREP 3 using Websockets """

import sys
import time
import getopt
import socket
import json
import websocket
import threading
import os
from threading import Thread, Event

# Global Default Variables
hostname = '127.0.0.1'
port = '15000'
user = 'root'
app_id = '256'
position = socket.gethostbyname(socket.gethostname())
post_servicename = 'TRCC'
post_itemname = 'CONTRIBUTION_RIC'
subscribe_servicename = 'ELEKTRON_DD'
subscribe_itemname = post_itemname

# Global Variables
next_post_time = 0
web_socket_app = None
web_socket_open = False
post_id = 1
bid_value = 34.25
ask_value = 35.48
primact_1_value = 116.50


#post_servicename = 'API_ATS'
#post_itemname = 'WASIN.BK'


def process_message(ws, message_json):
    """ Parse at high level and output JSON of message """
    message_type = message_json['Type']

    if message_type == "Refresh":
        if 'Domain' in message_json:
            message_domain = message_json['Domain']
            if message_domain == "Login":
                process_login_response(ws, message_json)
        elif message_json['Key']['Name'] == subscribe_itemname:
            # send Off Stream Post
            print("Sending Off-Stream Post to TREP Server")
            send_market_price_post(ws)
    elif message_type == "Ping":
        pong_json = {'Type': 'Pong'}
        ws.send(json.dumps(pong_json))
        print("SENT:")
        print(json.dumps(pong_json, sort_keys=True,
                         indent=2, separators=(',', ':')))

    # If our TRI stream is now open, we can start sending posts.
    global next_post_time
    if ('ID' in message_json and message_json['ID'] == 1 and next_post_time == 0 and
            (not 'State' in message_json or message_json['State']['Stream'] == "Open" and message_json['State']['Data'] == "Ok")):
        next_post_time = time.time() + 3
        print('Here')


def process_login_response(ws, message_json):
    """ Send item request """
    print("Sending Item Request to server")
    send_market_price_request(ws)
    # send Off Stream Post
    #print("Sending Off-Stream Post to TREP Server")
    # send_market_price_post(ws)


def send_market_price_request(ws):
    """ Create and send simple Market Price request """
    mp_req_json = {
        'ID': 2,
        'Key': {
            'Name': subscribe_itemname,
            'Service': subscribe_servicename
        },
        'Streaming': True
    }
    ws.send(json.dumps(mp_req_json))
    print("SENT:")
    print(json.dumps(mp_req_json, sort_keys=True, indent=2, separators=(',', ':')))


def send_market_price_post(ws):
    global post_id
    global bid_value
    global ask_value
    global primact_1_value
    """ Send a post message containing market-price content to TRCC """

    update_fields = {
        "BID": bid_value,
        "ASK": ask_value,
        "PRIMACT_1": primact_1_value
    }

    payload_json = {
        "ID": 0,
        "Type": "Update",
        "Domain": "MarketPrice",
        "Fields": update_fields,
        "Key": {
            "Name": post_itemname,
            "Service": post_servicename
        }
    }

    mp_post_json_offstream = {
        "Domain": "MarketPrice",
        "Ack": True,
        "PostID": post_id,
        "PostUserInfo": {
            "Address": "172.20.110.92",
            "UserID": 14736
        },
        "Key": {
            "Name": post_itemname,
            "Service": post_servicename
        },
        "Message": payload_json,
        "Type": "Post",
        "ID": 1
    }

    ws.send(json.dumps(mp_post_json_offstream))
    print("SENT:")
    print(json.dumps(mp_post_json_offstream,
                     sort_keys=True, indent=2, separators=(',', ':')))
    post_id += 1
    bid_value += 1
    ask_value += 1
    primact_1_value += 1


def send_login_request(ws):
    """ Generate a login request from command line data (or defaults) and send """
    login_json = {
        'ID': 1,
        'Domain': 'Login',
        'Key': {
            'Name': '',
            'Elements': {
                'ApplicationId': '',
                'Position': ''
            }
        }
    }

    login_json['Key']['Name'] = user
    login_json['Key']['Elements']['ApplicationId'] = app_id
    login_json['Key']['Elements']['Position'] = position

    ws.send(json.dumps(login_json))
    print("SENT:")
    print(json.dumps(login_json, sort_keys=True, indent=2, separators=(',', ':')))


def on_message(ws, message):
    """ Called when message received, parse message into JSON for processing """
    print("RECEIVED: ")
    message_json = json.loads(message)
    print(json.dumps(message_json, sort_keys=True, indent=2, separators=(',', ':')))

    for singleMsg in message_json:
        process_message(ws, singleMsg)


def on_error(ws, error):
    """ Called when websocket error has occurred """
    print(error)


def on_close(ws):
    """ Called when websocket is closed """
    global web_socket_open
    print("WebSocket Closed")
    web_socket_open = False


def on_open(ws):
    """ Called when handshake is complete and websocket is open, send login """

    print("WebSocket successfully connected!")
    global web_socket_open
    web_socket_open = True
    send_login_request(ws)


if __name__ == "__main__":

    # Get command line parameters
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", [
                                   "help", "hostname=", "port=", "app_id=", "user=", "position=", "item=", "post_service=", "item_service="])
        print(opts)
    except getopt.GetoptError:
        print(
            'Usage: market_price.py [--hostname hostname] [--port port] [--app_id app_id] [--user user] [--position position] [--item post/subscribe item name] [--post_service TRCC Post Service] [--item_service item subscription service] [--help] ')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("--help"):
            print(
                'Usage: market_price.py [--hostname hostname] [--port port] [--app_id app_id] [--user user] [--position position] [--item post/subscribe item name] [--post_service TRCC Post Service] [--item_service item subscription service] [--help]')
            sys.exit(0)
        elif opt in ("--hostname"):
            hostname = arg
        elif opt in ("--port"):
            port = arg
        elif opt in ("--app_id"):
            app_id = arg
        elif opt in ("--user"):
            user = arg
        elif opt in ("--position"):
            position = arg
        elif opt in ("--item"):
            post_itemname = subscribe_itemname = arg
        elif opt in ("--post_service"):
            post_servicename = arg
        elif opt in ("--item_service"):
            subscribe_servicename = arg

    # Start websocket handshake
    ws_address = "ws://{}:{}/WebSocket".format(hostname, port)
    print("Connecting to WebSocket " + ws_address + " ...")
    web_socket_app = websocket.WebSocketApp(ws_address, header=['User-Agent: Python'],
                                            on_message=on_message,
                                            on_error=on_error,
                                            on_close=on_close,
                                            subprotocols=['tr_json2'])
    web_socket_app.on_open = on_open

    # Event loop
    wst = threading.Thread(target=web_socket_app.run_forever)
    wst.start()

    try:
        while True:
            time.sleep(15)
            if next_post_time != 0 and time.time() > next_post_time:
                #print('if next_post_time != 0 and time.time() > next_post_time:')
                send_market_price_post(web_socket_app)
                next_post_time = time.time() + 3
    except KeyboardInterrupt:
        web_socket_app.close()
