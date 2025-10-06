# |-----------------------------------------------------------------------------
# |            This source code is provided under the Apache 2.0 license      --
# |  and is provided AS IS with no warranty or guarantee of fit for purpose.  --
# |                See the project's LICENSE.md for details.                  --
# |           Copyright LSEG 2025. All rights reserved.                       --
# |-----------------------------------------------------------------------------


#!/usr/bin/env python
""" Simple example of posting Market Price JSON data To RCC via LSEG Real-Time Distribution System 3.2.x using Websockets """

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
hostname = 'ADS_HOST'
port = '15000'
user = 'root'
app_id = '256'
position = socket.gethostbyname(socket.gethostname())
service_name = 'TRCC'
post_item_name = 'CONTRIBUTION_RIC'
login_id = 1

# Global Variables
next_post_time = 0
web_socket_app = None
web_socket_open = False
post_id = 1
bid_value = 34.25
ask_value = 35.48
primact_1_value = 116.50


def process_message(ws, message_json):  # Process all incoming messages.
    """ Parse at high level and output JSON of message """
    message_type = message_json['Type']

    if message_type == 'Refresh':
        if 'Domain' in message_json:
            message_domain = message_json['Domain']
            if message_domain == 'Login':
                process_login_response(ws, message_json)
    elif message_type == 'Ping':
        pong_json = {'Type': 'Pong'}
        ws.send(json.dumps(pong_json))
        print('SENT:')
        print(json.dumps(pong_json, sort_keys=True,
                         indent=2, separators=(',', ':')))

    #If our TRI stream is now open, we can start sending posts.
    global next_post_time
    if ('ID' in message_json and message_json['ID'] == 1 and next_post_time == 0 and
            (not 'State' in message_json or message_json['State']['Stream'] == 'Open' and message_json['State']['Data'] == 'Ok')):
        next_post_time = time.time() + 3
        print('Here')


# Process incoming Login Refresh Response message.
def process_login_response(ws, message_json):
    """ Send Off-Stream Post """
    print('Sending Off-Stream Post to Real-Time Advanced Distribution Server')
    send_market_price_post(ws)


# Create JSON Off-Stream Post message and sends it to ADS server.
def send_market_price_post(ws):
    global post_id
    global bid_value
    global ask_value
    global primact_1_value
    # Send a post message contains a market-price content to RCC

    # Contribution fields
    contribution_fields = {
        'BID': bid_value,
        'ASK': ask_value,
        'PRIMACT_1': primact_1_value
    }

    # OMM Post msg Key
    mp_post_key = {
        'Name': post_item_name,
        'Service': service_name
    }

    # OMM Post Payload
    contribution_payload_json = {
        'ID': 0,
        'Type': 'Update',
        'Domain': 'MarketPrice',
        'Fields': contribution_fields,
        'Key': {}
    }

    # OMM Off-Stream Post message
    mp_post_json_offstream = {
        'Domain': 'MarketPrice',
        'Ack': True,
        'PostID': post_id,
        'PostUserInfo': {
            'Address': position,
            'UserID': int(app_id)
        },
        'Key': {},
        'Message': {},
        'Type': 'Post',
        'ID': login_id
    }

    contribution_payload_json['Key'] = mp_post_key
    mp_post_json_offstream['Key'] = mp_post_key
    mp_post_json_offstream['Message'] = contribution_payload_json

    ws.send(json.dumps(mp_post_json_offstream))
    print('SENT:')
    print(json.dumps(mp_post_json_offstream,
                     sort_keys=True, indent=2, separators=(',', ':')))

    # increase post data value
    post_id += 1
    bid_value += 1
    ask_value += 1
    primact_1_value += 1


# Create JSON Login request message and sends it to ADS server.
def send_login_request(ws):
    """ Generate a login request from command line data (or defaults) and send """
    login_json = {
        'ID': login_id,
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
    print('SENT:')
    print(json.dumps(login_json, sort_keys=True, indent=2, separators=(',', ':')))


def on_message(ws, message):
    """ Called when message received, parse message into JSON for processing """
    print('RECEIVED: ')
    message_json = json.loads(message)
    print(json.dumps(message_json, sort_keys=True, indent=2, separators=(',', ':')))

    for singleMsg in message_json:
        process_message(ws, singleMsg)


def on_error(ws, error):
    """ Called when websocket error has occurred """
    print(error)


def on_close(ws, close_status_code, close_msg):
    """ Called when websocket is closed """
    global web_socket_open
    print(f'WebSocket Closed: {close_status_code} {close_msg}')
    web_socket_open = False


def on_open(ws):
    """ Called when handshake is complete and websocket is open, send login """

    print('WebSocket successfully connected!')
    global web_socket_open
    web_socket_open = True
    send_login_request(ws)


if __name__ == '__main__':

    # Get command line parameters
    try:
        opts, args = getopt.getopt(sys.argv[1:], '', [
                                   'help', 'hostname=', 'port=', 'app_id=', 'user=', 'position=', 'item=', 'service='])
        print(opts)
    except getopt.GetoptError:
        print(
            'Usage: market_price.py [--hostname hostname] [--port port] [--app_id app_id] [--user user] [--position position] [--item post item name] [--service TRCC Post Service]  [--help] ')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('--help'):
            print(
                'Usage: market_price.py [--hostname hostname] [--port port] [--app_id app_id] [--user user] [--position position] [--item post item name] [--service TRCC Post Service] [--help]')
            sys.exit(0)
        elif opt in ('--hostname'):
            hostname = arg
        elif opt in ('--port'):
            port = arg
        elif opt in ('--app_id'):
            app_id = arg
        elif opt in ('--user'):
            user = arg
        elif opt in ('--position'):
            position = arg
        elif opt in ('--item'):
            post_item_name = arg
        elif opt in ('--service'):
            service_name = arg

    # Start websocket handshake
    ws_address = f'ws://{hostname}:{port}/WebSocket'
    print(f'Connecting to WebSocket {ws_address} .... ')
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
            time.sleep(10)
            if next_post_time != 0 and time.time() > next_post_time:
                send_market_price_post(web_socket_app)
                next_post_time = time.time() + 3
    except KeyboardInterrupt:
        web_socket_app.close()
