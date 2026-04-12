from src.core.exceptions import ConflictError, NotFoundError
from src.domain.entities.service_plan import ServicePlan
from src.domain.entities.subscription import Subscription
from src.interfaces.repositories.account_telegram_link import IAccountTelegramLinkRepository
from src.interfaces.repositories.service_plan import IServicePlanRepository
from src.interfaces.repositories.subscription import ISubscriptionRepository


class ServicePlanService:
    __slots__ = ("_service_plan_repo", "_subscription_repo", "_link_repo")

    def __init__(
        self,
        service_plan_repo: IServicePlanRepository,
        subscription_repo: ISubscriptionRepository,
        link_repo: IAccountTelegramLinkRepository,
    ) -> None:
        self._service_plan_repo = service_plan_repo
        self._subscription_repo = subscription_repo
        self._link_repo = link_repo

    async def list_all(self) -> list[ServicePlan]:
        return await self._service_plan_repo.list_active()

    async def activate_trial(self, account_id: str) -> Subscription:
        trial = await self._service_plan_repo.get_trial()
        if trial is None:
            raise NotFoundError("Пробный период недоступен")

        if await self._subscription_repo.has_used_trial(account_id):
            raise ConflictError("Пробный период уже был активирован")

        telegram_user_id = await self._link_repo.get_telegram_id_by_account(account_id) or 0

        return await self._subscription_repo.create_for_account(
            account_id=account_id,
            telegram_user_id=telegram_user_id,
            service_id=trial.service_id,
            duration_days=trial.duration_days,
        )
