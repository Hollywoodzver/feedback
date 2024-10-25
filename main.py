
import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import config
from handlers import router
from database.models import async_main

logging.basicConfig(level=logging.INFO)






async def main():
    await async_main()
    bot = Bot(token=config.API_TOKEN)  # Используем API_TOKEN из config.py
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    
    # Запуск polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())