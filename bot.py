import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp
from aiogram.types import FSInputFile 
import psycopg2
from psycopg2.extras import RealDictCursor
import os

TOKEN = "8892438224:AAFWTg46NHeirJyf63OV7YV2hlyeAPrtiA0"

API_URL = "http://127.0.0.1:8000/code/"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATABASE_URL = os.environ.get("DATABASE_URL")
DB_CONN = psycopg2.connect(DATABASE_URL, sslmode='require')

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Привет! Я авто-помощник для Honda.\n"
        "Напиши мне код ошибки (например, P0171), и я расскажу, в чём проблема и как чинить. \n"
        "Так же ты можешь написать разработчику-хондоводу @sssssemkaa напрямую и предложить идею по усовершенствованию бота!\n\n"
        "/help - помощь.\n"
        "/about - о проекте.\n"
        "/weather - погода. \n"
    )

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "Пришли мне ошибку в формате P0000 и я подскажу, как её исправить!"
    )

@dp.message(Command("about"))
async def about_command(message: types.Message):
    photo = FSInputFile("img/about.jpg")
    await message.answer_photo(photo=photo, caption="Телеграм-бот для диагностики Honda с интеграцией базы данных и внешнего API.")

@dp.message(Command("weather"))
async def weather_command(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Напиши город после команды. Например: /weather Moscow", parse_mode="Markdown")
        return
    
    city = args[1].strip()
    
    async with aiohttp.ClientSession() as session:
        try:
            url = f"https://wttr.in/{city}?format=%C+%t+%w+%h"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.text()
                    
                    await message.answer(f"Погода в *{city}*:\n{data}", parse_mode="Markdown")
                else:
                    await message.answer("Не удалось получить погоду. Проверь название города.")
        except Exception as e:
            await message.answer(f"Ошибка соединения: {str(e)}")

@dp.message()
async def handle_code(message: types.Message):
    code = message.text.strip().upper()
    
    # Проверяем, похоже ли сообщение на код ошибки
    if not code.startswith("P") or not code[1:].isdigit():
        await message.answer("Пожалуйста, введи код ошибки в формате P0171 или P0300")
        return

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(API_URL + code) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "error" in data:
                        await message.answer(f"{data['error']}")
                        return
                    
                    danger_emojis = {1: "🔴", 2: "🔵", 3: "⚪"}
                    danger_text = {1: "Критично", 2: "Средне", 3: "Безопасно"}
                    danger_level = data.get("danger_level", 3)
                    
                    answer = (
                        f"*Код ошибки:* {data['code']}\n"
                        f"*Описание:* {data['description']}\n"
                        f"*Опасность:* {danger_emojis[danger_level]} {danger_text[danger_level]}\n"
                        f"*Совет:* {data['specific_advice']}"
                    )
                    
                    cursor = DB_CONN.cursor(cursor_factory=RealDictCursor)
                    cursor.execute(
                        "SELECT name, article, brand, price, url FROM parts WHERE error_code = %s",
                        [code]
                    )
                    parts = cursor.fetchall()
                    cursor.close()
                    
                    if parts:
                        answer += "\n\n *Запчасти для устранения:*\n"
                        for p in parts:
                            price_text = f"{p['price']} руб." if p['price'] else "цена не указана"
                            url_text = f" [Купить]({p['url']})" if p['url'] else ""
                            brand_text = f" ({p['brand']})" if p['brand'] else ""
                            answer += f"• {p['name']}{brand_text} — {price_text}{url_text}\n"
                    else:
                        answer += "\n\n *Запчасти для этой ошибки пока не добавлены в базу.*"
                    
                    await message.answer(answer, parse_mode="Markdown")
                    
                else:
                    await message.answer(" Сервер временно недоступен. Попробуй позже.")
        except Exception as e:
            await message.answer(f" Ошибка соединения: {str(e)}")



async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())