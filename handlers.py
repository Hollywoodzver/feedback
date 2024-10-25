import logging
from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from config import ADMIN_IDS
from keyboards import main_keyboard, admin_keyboard
from database.models import News, async_session

logging.basicConfig(level=logging.INFO)

router = Router()  # Инициализация Router
admin_ids = ADMIN_IDS

class Form(StatesGroup):
    waiting_for_text = State()

@router.message(CommandStart())
async def startcom(message: types.Message):
    if message.from_user.id in admin_ids:
        await message.answer("Сааламма админ жди просто")
    else:
        await message.answer("Здравствуйте, вы попали в предложку ХН!\nВыберите действие", reply_markup=main_keyboard())

@router.message(F.text == 'Отправить новость')
async def news(message: types.Message, state: FSMContext):
    await message.reply("Отправьте новость (желательно приложите скрины)")
    await state.set_state(Form.waiting_for_text)

@router.message(StateFilter(Form.waiting_for_text))
async def waitnews(message: types.Message, state: FSMContext):
    async with async_session() as session:
        new_news = News(user_id=message.from_user.id, text=message.text, status='waiting')
        session.add(new_news)
        await session.commit()
        session.refresh(new_news)
        news_id = new_news.id
    global user_u
    user_u = message.from_user.username
    admin_message = f'Новая новость номер {news_id}\nTelegram ID Отправителя: {message.from_user.id}, @{message.from_user.username}'
    for admin_id in admin_ids:
        await message.bot.forward_message(admin_id, from_chat_id=message.chat.id, message_id=message.message_id)
        await message.bot.send_message(admin_id, admin_message, reply_markup=admin_keyboard(news_id))
    await message.answer(f"Новость номер {news_id} отправлена на рассмотрение")
    await state.clear()

@router.callback_query()
async def confirm_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action, news_id = callback_query.data.split(":")
    async with async_session() as session:
        # Получаем новость по ID
        news_query = select(News).where(News.id == int(news_id))
        result = await session.execute(news_query)
        news = result.scalar_one_or_none()  # Получаем сам объект News


        if news:
                if action == "approve":
                    if news.status == 'waiting':
                        news.status = 'accepted'
                        await session.commit()
                        user_id = news.user_id

                        await callback_query.bot.send_message(
                            user_id,
                            text=f"Ваша новость номер {news_id} одобрена. Скоро она появится в нашем канале!"
                        ) 
                        await callback_query.message.edit_text(f"Одобрено для @{user_u} ({user_id})")
                        await callback_query.answer()
                    else:
                        await callback_query.answer(f"Новость номер {news_id} уже рассмотрена", show_alert=True) 
                        await callback_query.message.edit_text(f"Новость {news_id} уже рассмотрена") 
                        
                        
                if action == "reject":
                    if news.status == 'waiting':
                        news.status = 'rejected'
                        await session.commit()
                        user_id = news.user_id

                        await callback_query.bot.send_message(
                            user_id,
                            text=f"Ваша новость номер {news_id} отклонена"
                        ) 
                        await callback_query.message.edit_text(f"Отклоено для @{user_u} ({user_id})")
                        await callback_query.answer()
                    else:
                        await callback_query.answer(f"Новость номер {news_id} уже рассмотрена", show_alert=True) 
                        await callback_query.message.edit_text(f"Новость {news_id} уже рассмотрена")   
        
        else:
            await callback_query.answer("Ошибка: пользователь не найден", show_alert=True)  
            await callback_query.message.edit_text("не найдено")
            
