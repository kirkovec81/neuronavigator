import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from groq import Groq

# === Переменные окружения ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# === Инициализация ===
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

client = Groq(api_key=GROQ_API_KEY)


# === Функция запроса к ИИ ===
async def ask_ai(text):
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "user", "content": text}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content


# === Команда /start ===
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer("Привет! Я бесплатный ИИ-бот на Groq 🚀 Напиши мне что-нибудь.")


# === Ответ на любое сообщение ===
@dp.message()
async def handle_message(message: types.Message):
    try:
        answer = await ask_ai(message.text)
        await message.answer(answer)
    except Exception as e:
        await message.answer("Ошибка ИИ. Попробуй позже.")


# === Запуск ===
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
