from environs import Env
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config_data.config import DSN
from logger.logging_config import logger
from models.models import Base

env = Env()

# Глобальный singleton экземпляр базы данных
_db_instance = None


def get_database():
    """Получить singleton экземпляр базы данных."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DataBase()
    return _db_instance


class DataBase:
    def __init__(self):
        try:
            self.connect = DSN
            self.async_engine = create_async_engine(
                self.connect,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,  # Переиспользование соединений через час
                pool_pre_ping=True,  # Проверка соединений перед использованием
                echo=False
            )
            self.Session = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        except ArgumentError as e:
            logger.error(f"Invalid DSN configuration", e)
            raise

    async def create_db(self):
        async with self.async_engine.begin() as connect:
            await connect.run_sync(Base.metadata.create_all)

    async def close(self):
        await self.async_engine.dispose()
