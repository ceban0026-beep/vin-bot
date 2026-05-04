import os
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils import executor

API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

user_data = {}


# --- VIN → авто ---
def decode_vin(vin):
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
    r = requests.get(url).json()
    data = r['Results'][0]

    return {
        "make": data.get("Make"),
        "model": data.get("Model"),
        "year": data.get("ModelYear"),
        "engine": data.get("EngineModel")
    }


# --- Поиск по 999.md ---
def search_999(query):
    url = f"https://999.md/ru/list/auto-parts?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    results = []

    items = soup.select(".ads-list-photo-item-title")

    for item in items[:5]:
        title = item.get_text(strip=True)
        link = "https://999.md" + item.get("href")

        results.append(f"{title}\n{link}")

    return results


# --- Меню ---
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Ходовая", "Двигатель")
    return kb


def hodovaya_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Сайлентблок", "Амортизатор")
    return kb


# --- Обработчик ---
@dp.message_handler()
async def handler(message: types.Message):
    text = message.text.strip()

    # VIN
    if len(text) >= 10:
        car = decode_vin(text)

        if not car["make"]:
            await message.answer("❌ VIN не найден")
            return

        user_data[message.chat.id] = car

        await message.answer(
            f"🚗 {car['make']} {car['model']} {car['year']}\nДвигатель: {car['engine']}",
            reply_markup=main_menu()
        )
        return

    # Категории
    if text == "Ходовая":
        await message.answer("Выбери деталь:", reply_markup=hodovaya_menu())
        return

    # Детали
    if text in ["Сайлентблок", "Амортизатор"]:
        car = user_data.get(message.chat.id)

        if not car:
            await message.answer("Сначала введи VIN")
            return

        query = f"{text} {car['make']} {car['model']} {car['year']}"

        results = search_999(query)

        if not results:
            await message.answer("❌ Ничего не найдено")
            return

        await message.answer("💰 Результаты:\n\n" + "\n\n".join(results))


if __name__ == "__main__":
    executor.start_polling(dp)
# restart
