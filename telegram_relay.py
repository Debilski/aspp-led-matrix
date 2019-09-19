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

    socket.send_json(text)


client.start()
client.run_until_disconnected()
