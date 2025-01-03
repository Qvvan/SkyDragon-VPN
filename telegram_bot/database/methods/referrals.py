from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from logger.logging_config import logger
from models.models import Referrals, ReferralStatus


class ReferralMethods:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_referrer(self, referral: Referrals):
        try:
            self.session.add(referral)
            return True
        except IntegrityError as e:
            await logger.log_error(f"Integrity error when adding referral", e)
            return False
        except SQLAlchemyError as e:
            await logger.log_error(f"SQLAlchemy error when adding referral", e)
            return False

    async def get_list_referrers(self, referrer_id: int):
        if referrer_id is None:
            await logger.log_error("User ID is None", None)
            return False

        try:
            result = await self.session.execute(select(Referrals).where(Referrals.referrer_id == referrer_id))
            referrals = result.scalars().all()
            return referrals if referrals else []
        except SQLAlchemyError as e:
            await logger.log_error(f"Error fetching referrals", e)
            return False

    async def update_referral_status_if_invited(self, referred_id: int):
        try:
            # Fetch the referral entry
            query = select(Referrals).where(
                Referrals.referred_id == referred_id,
                Referrals.bonus_issued == ReferralStatus.INVITED
            )
            result = await self.session.execute(query)
            referral_entry = result.scalar_one_or_none()

            if referral_entry:
                await self.session.execute(
                    update(Referrals)
                    .where(Referrals.referred_id == referred_id)
                    .values(bonus_issued=ReferralStatus.SUBSCRIBED)
                )
                return referral_entry.referrer_id
            return False
        except SQLAlchemyError as error:
            await logger.log_error(f"Error updating referral status for referred_id {referred_id}", error)
            return False