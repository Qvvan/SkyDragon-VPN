from sqlalchemy import asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from logger.logging_config import logger
from models.models import Services


class ServiceMethods:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_services(self):
        try:
            result = await self.session.execute(select(Services).order_by(asc(Services.service_id)))
            services = result.scalars().all()
            return services
        except SQLAlchemyError as e:
            await logger.log_error(f"Ошибка получение услуги", e)
            return []

    async def get_service_by_id(self, service_id: int):
        try:
            result = await self.session.execute(
                select(Services).filter_by(service_id=service_id)
            )
            service = result.scalar_one_or_none()

            return service
        except Exception as e:
            await logger.log_error('Не удалось взять данную услугу', e)
            raise
