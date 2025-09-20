import asyncio
import aiohttp
import json
from typing import Dict, Any
from database import db, User
from config import BOT_TOKEN, TELEGRAM_GROUP, WEBINAR_LINK

class WebinarBot:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.session = None

    async def init(self):
        self.session = aiohttp.ClientSession()
        await db.init_db()

    async def close(self):
        if self.session:
            await self.session.close()

    async def make_request(self, method: str, data: Dict = None) -> Dict:
        url = f"{self.base_url}/{method}"
        async with self.session.post(url, json=data) as response:
            return await response.json()

    async def send_message(self, chat_id: int, text: str, 
                          reply_markup: Dict = None) -> Dict:
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        return await self.make_request("sendMessage", data)

    async def get_chat_member(self, chat_id: str, user_id: int) -> Dict:
        data = {
            "chat_id": chat_id,
            "user_id": user_id
        }
        return await self.make_request("getChatMember", data)

    def create_keyboard(self, buttons: list, one_time: bool = True) -> Dict:
        keyboard = []
        for button in buttons:
            if isinstance(button, list):
                row = [{"text": btn[0], "callback_data": btn[1]} for btn in button]
            else:
                row = [{"text": button[0], "callback_data": button[1]}]
            keyboard.append(row)
        
        return {
            "inline_keyboard": keyboard,
            "one_time_keyboard": one_time
        }

    async def handle_start(self, chat_id: int, user_data: Dict):
        user = await db.get_user(user_data['id'])
        if not user:
            await db.create_user(user_data)
        
        keyboard = self.create_keyboard([
            [("🎟️ Зарегистрироваться на вебинар", "register")],
            [("ℹ️ Справка", "help")]
        ])
        
        welcome_text = (
            "👋 Добро пожаловать в бот для регистрации на вебинар!\n\n"
            "Выберите действие:"
        )
        
        await self.send_message(chat_id, welcome_text, keyboard)

    async def handle_help(self, chat_id: int):
        help_text = (
            "ℹ️ <b>Справка по боту</b>\n\n"
            "Этот бот помогает зарегистрироваться на вебинар.\n\n"
            "Для регистрации:\n"
            "1. Нажмите 'Зарегистрироваться на вебинар'\n"
            "2. Вступите в нашу Telegram-группу\n"
            "3. Вернитесь в бот и завершите регистрацию\n\n"
            "После успешной регистрации вы получите ссылку на вебинар."
        )
        
        keyboard = self.create_keyboard([
            [("🔙 Назад", "back_to_main")]
        ])
        
        await self.send_message(chat_id, help_text, keyboard)

    async def handle_register(self, chat_id: int, user_id: int):
        try:
            member_info = await self.get_chat_member(TELEGRAM_GROUP, user_id)
            is_subscribed = member_info.get('result', {}).get('status') in ['member', 'administrator', 'creator']
            
            if is_subscribed:
                await db.update_user_subscription(user_id, True)
                await db.update_user_registration(user_id, True)
                
                success_text = (
                    "✅ <b>Регистрация успешна!</b>\n\n"
                    f"Ссылка на вебинар: {WEBINAR_LINK}\n\n"
                    "Ждем вас на мероприятии!"
                )
                await self.send_message(chat_id, success_text)
                await self.handle_start(chat_id, {"id": user_id})
            else:
                subscribe_text = (
                    "📋 <b>Регистрация на вебинар</b>\n\n"
                    "Для завершения регистрации необходимо вступить в нашу Telegram-группу:\n"
                    f"{TELEGRAM_GROUP}\n\n"
                    "После вступления нажмите кнопку 'Проверить подписку'"
                )
                
                keyboard = self.create_keyboard([
                    [("🔗 Перейти в группу", f"url:https://t.me/{TELEGRAM_GROUP.lstrip('@')}")],
                    [("✅ Проверить подписку", "check_subscription")],
                    [("🔙 Назад", "back_to_main")]
                ])
                
                await self.send_message(chat_id, subscribe_text, keyboard)
                
        except Exception as e:
            error_text = (
                "❌ <b>Ошибка проверки подписки</b>\n\n"
                "Пожалуйста, убедитесь что группа существует и бот имеет к ней доступ."
            )
            await self.send_message(chat_id, error_text)

    async def handle_check_subscription(self, chat_id: int, user_id: int):
        try:
            member_info = await self.get_chat_member(TELEGRAM_GROUP, user_id)
            is_subscribed = member_info.get('result', {}).get('status') in ['member', 'administrator', 'creator']
            
            if is_subscribed:
                await db.update_user_subscription(user_id, True)
                await db.update_user_registration(user_id, True)
                
                success_text = (
                    "✅ <b>Спасибо за подписку!</b>\n\n"
                    "Регистрация на вебинар завершена успешно!\n\n"
                    f"Ссылка на вебинар: {WEBINAR_LINK}\n\n"
                    "Ждем вас на мероприятии!"
                )
                await self.send_message(chat_id, success_text)
                await self.handle_start(chat_id, {"id": user_id})
            else:
                not_subscribed_text = (
                    "❌ <b>Вы еще не подписались на группу</b>\n\n"
                    f"Пожалуйста, вступите в группу {TELEGRAM_GROUP} и попробуйте снова."
                )
                
                keyboard = self.create_keyboard([
                    [("🔗 Перейти в группу", f"url:https://t.me/{TELEGRAM_GROUP.lstrip('@')}")],
                    [("🔄 Проверить еще раз", "check_subscription")],
                    [("🔙 Назад", "back_to_main")]
                ])
                
                await self.send_message(chat_id, not_subscribed_text, keyboard)
                
        except Exception as e:
            error_text = (
                "❌ <b>Ошибка проверки подписки</b>\n\n"
                "Не удалось проверить подписку. Попробуйте позже."
            )
            await self.send_message(chat_id, error_text)

    async def process_update(self, update: Dict):
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            user_data = message["from"]
            
            if "text" in message:
                text = message["text"]
                if text.startswith("/start"):
                    await self.handle_start(chat_id, user_data)
        
        elif "callback_query" in update:
            callback_query = update["callback_query"]
            data = callback_query["data"]
            chat_id = callback_query["message"]["chat"]["id"]
            user_id = callback_query["from"]["id"]
            
            if data == "register":
                await self.handle_register(chat_id, user_id)
            elif data == "help":
                await self.handle_help(chat_id)
            elif data == "back_to_main":
                await self.handle_start(chat_id, {"id": user_id})
            elif data == "check_subscription":
                await self.handle_check_subscription(chat_id, user_id)
            
            await self.make_request("answerCallbackQuery", {
                "callback_query_id": callback_query["id"]
            })

async def main():
    bot = WebinarBot(BOT_TOKEN)
    await bot.init()
    
    print("Бот запущен...")
    
    offset = 0
    try:
        while True:
            try:
                updates = await bot.make_request("getUpdates", {
                    "offset": offset,
                    "timeout": 30
                })
                
                if updates.get("ok") and updates.get("result"):
                    for update in updates["result"]:
                        offset = update["update_id"] + 1
                        await bot.process_update(update)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Ошибка: {e}")
                await asyncio.sleep(5)
                
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())