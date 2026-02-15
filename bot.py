import asyncio
import os
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from openai import OpenAI

# ================== ЗАГРУЗКА ПЕРЕМЕННЫХ ==================

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
import os

ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_API_KEY)

# ================== БАЗА ДАННЫХ ==================

conn = sqlite3.connect("stats.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    user_id INTEGER,
    username TEXT,
    category TEXT,
    question TEXT
)
""")
conn.commit()

def log_question(user_id, username, category, question):
    cursor.execute("""
        INSERT INTO questions (date, user_id, username, category, question)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        user_id,
        username,
        category,
        question
    ))
    conn.commit()

# ================== КЛАВИАТУРА ==================

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📚 База знаний")],
        [KeyboardButton(text="🆘 Срочная помощь")],
        [KeyboardButton(text="☕ Для родителей")],
        [KeyboardButton(text="❓ Задать вопрос")],
        [KeyboardButton(text="📊 Статистика")]
    ],
    resize_keyboard=True
)

# ================== КЛАССИФИКАЦИЯ ==================

async def classify_question(question: str):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """Определи категорию вопроса. Ответь ОДНИМ словом из списка:

basics
sensory
communication
school
emotions
social
daily
interests
parent
therapy
teens
legal

Ничего кроме одного слова не пиши."""
            },
            {"role": "user", "content": question}
        ],
        temperature=0
    )

    return completion.choices[0].message.content.strip().lower()

# ================== ПРИВЕТСТВИЕ ==================

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        """Здравствуйте! Я — НейроНавигатор 🧠

Ваш цифровой помощник по вопросам РАС и СДВГ.

Задайте любой вопрос — я отвечу по структуре:
Причина
Что делать

Выберите раздел или напишите вопрос."""
        ,
        reply_markup=main_keyboard
    )

# ================== ОБРАБОТЧИКИ КНОПОК ==================

@dp.message(lambda message: message.text == "🆘 Срочная помощь")
async def meltdown_help(message: types.Message):
    await message.answer(
        """📌 Причина:
Мелтдаун возникает из-за сенсорной перегрузки или эмоционального перенапряжения.

✅ Что делать:
- Уберите лишние стимулы (свет, шум).
- Уведите в тихое место.
- Говорите короткими фразами.
- Не объясняйте в пик кризиса.
- Дайте время восстановиться."""
    )

@dp.message(lambda message: message.text == "☕ Для родителей")
async def parent_support(message: types.Message):
    await message.answer(
        """📌 Причина:
Эмоциональное выгорание возникает из-за хронического стресса.

✅ Что делать:
- Выделяйте время для отдыха ежедневно.
- Просите помощи.
- Поддерживайте режим сна.
- Обсуждайте трудности со специалистом."""
    )

# ================== СТАТИСТИКА (ТОЛЬКО ДЛЯ АДМИНА) ==================

@dp.message(lambda message: message.text == "📊 Статистика")
async def show_stats(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return

    cursor.execute("SELECT COUNT(*) FROM questions")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT category, COUNT(*)
        FROM questions
        GROUP BY category
        ORDER BY COUNT(*) DESC
    """)
    category_stats = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*) FROM questions
        WHERE date >= datetime('now', '-7 days')
    """)
    last_week = cursor.fetchone()[0]

    text = f"📊 Статистика НейроНавигатора\n\n"
    text += f"Всего вопросов: {total}\n"
    text += f"За 7 дней: {last_week}\n\n"
    text += "Категории:\n"

    for cat, count in category_stats:
        text += f"- {cat}: {count}\n"

    await message.answer(text)

# ================== ОСНОВНАЯ ЛОГИКА ==================

@dp.message()
async def handle_message(message: types.Message):

    user_question = message.text

    category = await classify_question(user_question)

    log_question(
        message.from_user.id,
        message.from_user.username,
        category,
        user_question
    )

    base_prompt = """Ты НейроНавигатор — ассистент по вопросам РАС и СДВГ.

Правила:
1. Если медицинский вопрос — опирайся на доказательную медицину.
2. Если бытовой — давай пошаговый алгоритм.
3. Если юридический — укажи на необходимость проверки законодательства.
4. Всегда дели ответ на:
Причина
Что делать
Используй списки.
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": base_prompt},
            {"role": "user", "content": user_question}
        ],
        temperature=0.4
    )

    response = completion.choices[0].message.content
    response += "\n\n— НейроНавигатор 🧠"

    await message.answer(response)

# ================== ЗАПУСК ==================

async def main():
    print("НейроНавигатор запущен 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
