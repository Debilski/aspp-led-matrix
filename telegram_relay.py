import json
import os
import sys
from pathlib import Path

import zmq

from telethon import TelegramClient, events

api = json.loads(Path(os.environ['API_KEYS']).read_text())

api_id = api['api_id']
api_hash = api['api_hash']
CHAT_ID = api['chat_id']

SOCKET_ADDR = sys.argv[1]

client = TelegramClient('tridymite', api_id, api_hash)

ctx = zmq.Context()
socket = ctx.socket(zmq.PUB)
socket.bind(SOCKET_ADDR)

from netifaces import interfaces, ifaddresses, AF_INET

def ip4_addresses():
    ip_list = []
    for interface in interfaces():
        if interface.startswith('lo'):
            continue
        ip_list.append(ifaddresses(interface))
    return ip_list

async def main():
    # Getting information about yourself
    me = await client.get_me()

    # "me" is an User object. You can pretty-print
    # any Telegram object with the "stringify" method:
    print(me.stringify())

@client.on(events.NewMessage(chats=CHAT_ID))
async def my_event_handler(event):
    chat = await event.get_chat()
    sender = await event.get_sender()
    print(sender)
    text = event.raw_text
    chat_id = event.chat_id
    sender_id = event.sender_id
    photo = event.photo
    print("Received", text, flush=True)
    if text == '!ip':
        await event.reply(str(ip4_addresses()))
    elif photo:
        print(photo)
        download_res = await client.download_media(photo, '/tmp/telethon')
        print("Download done: {}".format(download_res))
        msg = f"/addimage {text} {download_res}"
        socket.send_json(msg)
    else:
        socket.send_json(text)

client.start()
client.run_until_disconnected()

