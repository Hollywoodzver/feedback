from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import BigInteger, String

# Инициализация асинхронного движка
engine = create_async_engine("sqlite+aiosqlite:///db.sqlite3", echo=True)

# Создаем асинхронный фабричный метод для сессий
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)

class Banned(Base):
    __tablename__ = 'blocked_users'
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger) 

class News(Base):
    __tablename__ = 'news'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(BigInteger)  # tg_id отправителя
    text = mapped_column(String)        # Текст новости
    status = mapped_column(String)

    
async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
