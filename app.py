import os
import json
import sqlite3
import requests
import uvicorn
from aiogram import Bot, Dispatcher, types, executor

API_TOKEN = '7530000682:AAGsCkknHnyFxsEZ7HLWk50O2TkXsPDCmSM'
WEBHOOK_URL = "https://5ab2-90-156-162-19.ngrok-free.app/webhook/"

bot = Bot(token=API_TOKEN)
Bot.set_current(bot)
dp = Dispatcher(bot)

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)''')
conn.commit()

def add_user_to_db(user_id):

    cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    conn.commit()

def get_users():
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()
    return [user[0] for user in users]

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    add_user_to_db(user_id)
    await message.answer("Xush kebsiz!")

async def send_message_users(chats_id, text):
    for chat_id in chats_id:
        try:
            await bot.send_message(chat_id, text)
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {e}")

async def app(scope, receive, send):
    if scope['type'] == 'http':
        if scope['path'] == '/send/' and scope['method'] == 'POST':
            body = b''
            more_body = True
            while more_body:
                message = await receive()
                body += message.get('body', b'')
                more_body = message.get('more_body', False)

            data = json.loads(body)
            message = data['message']
            chat_ids = get_users()

            await send_message_users(chat_ids, message)
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [
                    [b'content-type', b'application/json'],
                ],
            })
            await send({
                'type': 'http.response.body',
                'body': b'{"status":"ok"}',
            })

        elif scope['path'] == '/webhook/' and scope['method'] == 'POST':
            body = b''
            more_body = True
            while more_body:
                message = await receive()
                body += message.get('body', b'')
                more_body = message.get('more_body', False)

            update = json.loads(body)
            await dp.process_update(types.Update(**update))

            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [
                    [b'content-type', b'application/json'],
                ],
            })
            await send({
                'type': 'http.response.body',
                'body': b'{"status":"ok"}',
            })
        else:
            await send({
                'type': 'http.response.start',
                'status': 404,
                'headers': [
                    [b'content-type', b'text/plain'],
                ],
            })
            await send({
                'type': 'http.response.body',
                'body': b'Not found',
            })

if __name__ == "__main__":
    mode = os.getenv('MODE', 'webhook')
    if mode == 'webhook':
        requests.get(f"https://api.telegram.org/bot{API_TOKEN}/setWebhook?url={WEBHOOK_URL}")
        uvicorn.run("app:app", host="0.0.0.0", port=8000)
    else:
        requests.get(f"https://api.telegram.org/bot{API_TOKEN}/deleteWebhook")
        executor.start_polling(dp, skip_updates=True)
