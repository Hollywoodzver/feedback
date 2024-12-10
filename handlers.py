import logging

from aiogram import F, types, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from config import ADMIN_IDS
from database.models import News, async_session, User, Banned, engine
from keyboards import main_keyboard, admin_keyboard


logging.basicConfig(level=logging.INFO)

router = Router()  # Инициализация Router
admin_ids = ADMIN_IDS

class Form(StatesGroup):
    waiting_for_text = State()

async def is_user_banned(user_id: int) -> bool:
    async with async_session() as session:
        stmt = select(Banned).where(Banned.tg_id == user_id)
        result = await session.execute(stmt)
        banned_user = result.scalar_one_or_none()  # Возвращает объект или None
        return banned_user is not None

@router.message(CommandStart())
async def startcom(message: types.Message):
    if message.from_user.id in admin_ids:
        await message.answer("Сааламма админ жди просто")
    else:
        async with async_session() as session:
            # Проверяем, существует ли пользователь
            stmt = select(User).where(User.tg_id == message.from_user.id)
            result = await session.execute(stmt)
            exists = result.scalar_one_or_none()  # Возвращает запись или None
        if not exists:
            async with async_session() as session:
                id_users = User(tg_id=message.from_user.id, tg_us = message.from_user.username)
                session.add(id_users)
                await session.commit()
                session.refresh(id_users)
        await message.answer("Здравствуйте, вы попали в предложку ХН!\nВыберите действие", reply_markup=main_keyboard())

   
@router.message(F.text == 'Отправить новость')
async def news(message: types.Message, state: FSMContext):
    if await is_user_banned(message.from_user.id):
        await message.reply("🚫 Вы заблокированы и не можете отправлять сообщения")
        return
    await message.reply("Отправьте новость (желательно приложите скрины)")
    await state.set_state(Form.waiting_for_text)

@router.message(StateFilter(Form.waiting_for_text))
async def waitnews(message: types.Message, state: FSMContext):
    async with async_session() as session:
        new_news = News(user_us=message.from_user.username ,user_id=message.from_user.id, text=message.text, status='waiting')
        session.add(new_news)
        await session.commit()
        session.refresh(new_news)
        news_id = new_news.id
        await state.update_data(user_u=message.from_user.username)
    admin_message = f'Новая новость номер {news_id}\nTelegram ID Отправителя: {message.from_user.id}, @{message.from_user.username}'
    for admin_id in admin_ids:
        await message.bot.forward_message(admin_id, from_chat_id=message.chat.id, message_id=message.message_id)
        await message.bot.send_message(admin_id, admin_message, reply_markup=admin_keyboard(news_id))
    await message.answer(f"Новость номер {news_id} отправлена на рассмотрение")
 

@router.callback_query()
async def confirm_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action, news_id = callback_query.data.split(":")
    async with async_session() as session:
        # Получаем новость по ID
        news_query = select(News).where(News.id == int(news_id))
        result = await session.execute(news_query)
        news = result.scalar_one_or_none()  # Получаем сам объект News

        if news:
        
                usern = news.user_us
                if action == "approve":
                    if news.status == 'waiting':
                        news.status = 'accepted'
                        await session.commit()
                        user_id = news.user_id

                        await callback_query.bot.send_message(
                            user_id,
                            text=f"Ваша новость номер {news_id} одобрена. Скоро она появится в нашем канале!"
                        ) 
                        await callback_query.message.edit_text(f"Одобрено для @{usern} ({user_id})")
                        await callback_query.answer()
                    else:
                        await callback_query.answer(f"Новость номер {news_id} уже рассмотрена", show_alert=True) 
                        await callback_query.message.edit_text(f"Новость {news_id} уже рассмотрена") 
                        
                        
                elif action == "reject":
                    if news.status == 'waiting':
                        news.status = 'rejected'
                        await session.commit()
                        user_id = news.user_id

                        await callback_query.bot.send_message(
                            user_id,
                            text=f"Ваша новость номер {news_id} отклонена"
                        ) 
                        await callback_query.message.edit_text(f"Отклонено для @{usern} ({user_id})")
                        await callback_query.answer()
                    else:
                        await callback_query.answer(f"Новость номер {news_id} уже рассмотрена", show_alert=True) 
                        await callback_query.message.edit_text(f"Новость {news_id} уже рассмотрена") 

                else:
                    if news.status == 'waiting':
                        news.status = 'banned'
                        id_users = Banned(tg_id=news.user_id)
                        session.add(id_users)
                        await session.commit()
                        session.refresh(id_users)
                        user_id = news.user_id
                        await callback_query.message.edit_text(f"Пользователь @{usern} ({user_id}) заблокирован.")
                        await callback_query.bot.send_message(
                                user_id,
                                text=f"🚫 Вы были заблокированы."
                            )
                    else:
                        await callback_query.answer(f"Новость номер {news_id} уже рассмотрена", show_alert=True) 
                        await callback_query.message.edit_text(f"Новость {news_id} уже рассмотрена") 
        
        else:
            await callback_query.answer("Ошибка: пользователь не найден", show_alert=True)  
            await callback_query.message.edit_text("не найдено")
