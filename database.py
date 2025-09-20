from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_subscribed = Column(Boolean, default=False)
    is_registered = Column(Boolean, default=False)

class Database:
    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_user(self, user_id):
        async with self.async_session() as session:
            result = await session.execute(
                f"SELECT * FROM users WHERE user_id = {user_id}"
            )
            user = result.fetchone()
            return user

    async def create_user(self, user_data):
        async with self.async_session() as session:
            user = User(
                user_id=user_data['id'],
                username=user_data.get('username'),
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name')
            )
            session.add(user)
            await session.commit()
            return user

    async def update_user_subscription(self, user_id, is_subscribed):
        async with self.async_session() as session:
            await session.execute(
                f"UPDATE users SET is_subscribed = {is_subscribed} WHERE user_id = {user_id}"
            )
            await session.commit()

    async def update_user_registration(self, user_id, is_registered):
        async with self.async_session() as session:
            await session.execute(
                f"UPDATE users SET is_registered = {is_registered} WHERE user_id = {user_id}"
            )
            await session.commit()

db = Database()