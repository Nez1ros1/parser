import asyncio
import logging
from telethon import TelegramClient, functions, types, errors
from aiogram import Bot, Dispatcher, types as aiotypes
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
API_ID = 33800259
API_HASH = '63b842b9ed4510d53d3badd9393be9d0'
BOT_TOKEN = '8555310755:AAHQplj0UE3w3JFsMpvCjhqIQWw4CJOQtQo'

# База женских имен и ников (50+ штук)
FEMALE_KEYWORDS = [
    'катя', 'екатерина', 'катюша', 'галя', 'галина', 'маша', 'мария', 'маришка',
    'анна', 'аня', 'анюта', 'света', 'светлана', 'светик', 'лена', 'елена', 
    'оля', 'ольга', 'олечка', 'наташа', 'наталья', 'натали', 'юля', 'юлия', 
    'юляша', 'даша', 'дарья', 'дашуля', 'ира', 'ирина', 'иришка', 'настя', 
    'анастасия', 'настюша', 'таня', 'татьяна', 'танечка', 'вика', 'виктория', 
    'лиза', 'елизавета', 'полина', 'поля', 'соня', 'софия', 'карина', 'алина', 
    'кристина', 'крис', 'алла', 'вероника', 'ника', 'марина', 'маришка',
    'лапусик', 'кисуля', 'киса', 'зая', 'зайка', 'солнышко', 'малышка', 
    'крошка', 'милашка', 'красотка', 'любимая', 'принцесса', 'куколка', 
    'лапочка', 'кошечка', 'baby', 'girl', 'princess'
]

# Вторая база: Недопустимые слова в нике
FORBIDDEN_KEYWORDS = ['nft', 'def', 'ton', 'crypto', 'drop', 'sale', 'bot', 'channel']

# Инициализация
client = TelegramClient('parser_session', API_ID, API_HASH)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

def check_user_criteria(user, profile_full):
    """Логика фильтрации пользователя"""
    first_name = (user.first_name or "").lower()
    last_name = (user.last_name or "").lower()
    username = (user.username or "").lower()
    full_text = f"{first_name} {last_name} {username}"

    # 1. Проверка на недопустимые слова (NFT, def, ton)
    if any(word in username for word in FORBIDDEN_KEYWORDS):
        return False

    # 2. Проверка на женские имена в нике или имени
    if not any(word in full_text for word in FEMALE_KEYWORDS):
        return False

    # 3. Проверка на NFT ЮЗЕРНЕЙМ (если куплен на Fragment - пропускаем)
    if user.usernames:
        for u in user.usernames:
            if getattr(u, 'collectible', False):
                return False

    # 4. Проверка подарков (Star Gifts)
    nft_gifts_count = 0
    regular_gifts_count = 0
    
    if hasattr(profile_full, 'star_gifts'):
        for gift in profile_full.star_gifts:
            if getattr(gift, 'nft', False):
                nft_gifts_count += 1
            else:
                regular_gifts_count += 1

    # УСЛОВИЕ: 1-2 NFT подарка (Дошик, Мороженое и др.) И до 150 обычных
    if 1 <= nft_gifts_count <= 2 and regular_gifts_count <= 150:
        return True
    
    return False

@dp.message(Command("start"))
async def cmd_start(message: aiotypes.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="🚀 Начать парсинг")
    await message.answer(
        "💎 **Бот-парсер активен**\n\n"
        "Ищу: Женщин с 1-2 NFT подарками.\n"
        "Фильтр: Без NFT-юзернеймов, стоп-слова (NFT, def, ton).\n"
        "Лимит обычных подарков: до 150.\n\n"
        "Нажми кнопку ниже, чтобы начать.", 
        reply_markup=builder.as_markup(resize_keyboard=True),
        parse_mode="Markdown"
    )

@dp.message(lambda m: m.text == "🚀 Начать парсинг")
async def ask_for_chat(message: aiotypes.Message):
    await message.answer("Пришли ссылку на чат (например, `@название_чата` или ссылку `t.me/...`), откуда собирать людей:")

@dp.message()
async def process_parsing(message: aiotypes.Message):
    if not (message.text.startswith('@') or 't.me/' in message.text):
        return

    target = message.text.replace('https://t.me/', '@')
    await message.answer(f"🔎 Начинаю анализ чата {target}...\nЭто может занять время из-за лимитов Telegram.")
    
    found_count = 0
    async with client:
        try:
            # Лимит 1000 участников для одной сессии парсинга
            async for user in client.iter_participants(target, limit=1000):
                if user.bot or user.deleted:
                    continue
                
                try:
                    # Запрос полной информации профиля (нужен для списка подарков)
                    full_info = await client(functions.users.GetFullUserRequest(id=user.id))
                    
                    if check_user_criteria(user, full_info.full_user):
                        contact = f"@{user.username}" if user.username else f"ID: {user.id}"
                        
                        # Бот присылает результат тебе в чат
                        await message.answer(
                            f"✅ **Найдена цель!**\n"
                            f"👤 Имя: {user.first_name}\n"
                            f"🔗 Юзернейм: {contact}\n"
                            f"🎁 Проверка: Прошла (1-2 NFT)"
                        )
                        found_count += 1
                    
                    # ОБЯЗАТЕЛЬНАЯ ПАУЗА, чтобы Telegram не забанил за частые запросы
                    await asyncio.sleep(2.5) 
                    
                except errors.FloodWaitError as e:
                    logging.warning(f"Ждем {e.seconds} секунд...")
                    await asyncio.sleep(e.seconds)
                except Exception:
                    continue
                    
            await message.answer(f"🏁 Парсинг завершен!\nВсего найдено подходящих: {found_count}")
            
        except Exception as e:
            await message.answer(f"❌ Ошибка при доступе к чату: {e}")

async def main():
    # Запуск клиента Telethon
    await client.start()
    print("Аккаунт авторизован. Бот запущен.")
    # Запуск бота Aiogram
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass