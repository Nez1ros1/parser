
import os
import asyncio
from telethon import TelegramClient, functions, types
from dotenv import load_dotenv

# Загрузка ключей из .env
load_dotenv()
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')

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
    'лапочка', 'кошечка', 'baby', 'girl', 'princess' "табалапка", "куроми", "тигрица" "замужем", "эльнара", 
"pretty", "уля", "ульяна" "ева", "рай"]

async def main():
    # Используем файл сессии, который ты создал
    client = TelegramClient('parser_session', API_ID, API_HASH)
    
    await client.start()
    print("Бот запущен! Начинаю глобальный поиск...")
    print("Для остановки нажми Ctrl+C (на ПК) или кнопку Стоп на хостинге.")

    found_users = []
    limit = 10 # Лимит 10 человек

    try:
        for name in NAMES_TO_SEARCH:
            if len(found_users) >= limit:
                break
                
            print(f"--- Ищу по имени: {name} ---")
            
            # Глобальный поиск по контактам (люди, которых нет в твоей книге)
            result = await client(functions.contacts.SearchRequest(
                q=name,
                limit=100
            ))

            for user in result.users:
                if len(found_users) >= limit:
                    break

                # Фильтры: не бот, не удален, есть юзернейм
                if not user.bot and not user.deleted and user.username:
                    try:
                        # Получаем полную информацию о профиле (для проверки подарков)
                        full_info = await client(functions.users.GetFullUserRequest(id=user.id))
                        
                        # Простая проверка: есть ли упоминание NFT в описании или спец. полях
                        # (В Telegram API подарки скрыты в GetFullUserRequest -> gifts)
                        about = full_info.full_user.about or ""
                        
                        # Логика: ищем тех, у кого мало подарков (признак недорогих NFT до 10 TON)
                        # Здесь можно добавить проверку конкретных названий коллекций
                        if "NFT" in about.upper() or "GIFT" in about.upper():
                            user_link = f"https://t.me/{user.username}"
                            if user_link not in found_users:
                                found_users.append(user_link)
                                print(f"[{len(found_users)}] Нашел подходящего: {user_link}")
                                
                    except Exception:
                        continue
            
            # Небольшая пауза между именами, чтобы Telegram не забанил
            await asyncio.sleep(2)

    except KeyboardInterrupt:
        print("\nПоиск приостановлен пользователем.")

    print("\n--- ИТОГОВЫЙ СПИСОК (10 человек) ---")
    for link in found_users:
        print(link)
    
    print("\nРабота завершена. Бот остается в сети. Чтобы выключить — останови контейнер.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
