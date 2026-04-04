"""Репозитории поверх Postgres (IQueryExecutor)."""

from core.container.infrastructure import InfrastructureContainer
from infrastructure.postgres.repository.gift_repository import PostgresGiftRepository
from infrastructure.postgres.repository.payment_repository import PostgresPaymentRepository
from infrastructure.postgres.repository.push_log_repository import PostgresPushLogRepository
from infrastructure.postgres.repository.referral_repository import PostgresReferralRepository
from infrastructure.postgres.repository.server_repository import PostgresServerRepository
from infrastructure.postgres.repository.service_tariff_repository import PostgresServiceTariffRepository
from infrastructure.postgres.repository.subscription_history_repository import PostgresSubscriptionHistoryRepository
from infrastructure.postgres.repository.subscription_repository import PostgresSubscriptionRepository
from infrastructure.postgres.repository.user_notification_repository import PostgresUserNotificationRepository
from infrastructure.postgres.repository.user_repository import PostgresUserRepository
from interfaces.repositories.gift_repository import IGiftRepository
from interfaces.repositories.payment_repository import IPaymentRepository
from interfaces.repositories.push_log_repository import IPushLogRepository
from interfaces.repositories.referral_repository import IReferralRepository
from interfaces.repositories.server_repository import IServerRepository
from interfaces.repositories.service_tariff_repository import IServiceTariffRepository
from interfaces.repositories.subscription_history_repository import ISubscriptionHistoryRepository
from interfaces.repositories.subscription_repository import ISubscriptionRepository
from interfaces.repositories.user_notification_repository import IUserNotificationRepository
from interfaces.repositories.user_repository import IUserRepository


class RepositoryContainer:
    __slots__ = (
        "_infra",
        "_subscription_repo",
        "_server_repo",
        "_tariff_repo",
        "_payment_repo",
        "_user_repo",
        "_gift_repo",
        "_referral_repo",
        "_subscription_history_repo",
        "_push_log_repo",
        "_user_notification_repo",
    )

    def __init__(self, infra: InfrastructureContainer) -> None:
        self._infra = infra
        self._subscription_repo: PostgresSubscriptionRepository | None = None
        self._server_repo: PostgresServerRepository | None = None
        self._tariff_repo: PostgresServiceTariffRepository | None = None
        self._payment_repo: PostgresPaymentRepository | None = None
        self._user_repo: PostgresUserRepository | None = None
        self._gift_repo: PostgresGiftRepository | None = None
        self._referral_repo: PostgresReferralRepository | None = None
        self._subscription_history_repo: PostgresSubscriptionHistoryRepository | None = None
        self._push_log_repo: PostgresPushLogRepository | None = None
        self._user_notification_repo: PostgresUserNotificationRepository | None = None

    @property
    def subscription_repository(self) -> ISubscriptionRepository:
        if not self._subscription_repo:
            self._subscription_repo = PostgresSubscriptionRepository(self._infra.query_executor)
        return self._subscription_repo

    @property
    def server_repository(self) -> IServerRepository:
        if not self._server_repo:
            self._server_repo = PostgresServerRepository(self._infra.query_executor)
        return self._server_repo

    @property
    def service_tariff_repository(self) -> IServiceTariffRepository:
        if not self._tariff_repo:
            self._tariff_repo = PostgresServiceTariffRepository(self._infra.query_executor)
        return self._tariff_repo

    @property
    def payment_repository(self) -> IPaymentRepository:
        if not self._payment_repo:
            self._payment_repo = PostgresPaymentRepository(self._infra.query_executor)
        return self._payment_repo

    @property
    def user_repository(self) -> IUserRepository:
        if not self._user_repo:
            self._user_repo = PostgresUserRepository(self._infra.query_executor)
        return self._user_repo

    @property
    def gift_repository(self) -> IGiftRepository:
        if not self._gift_repo:
            self._gift_repo = PostgresGiftRepository(self._infra.query_executor)
        return self._gift_repo

    @property
    def referral_repository(self) -> IReferralRepository:
        if not self._referral_repo:
            self._referral_repo = PostgresReferralRepository(self._infra.query_executor)
        return self._referral_repo

    @property
    def subscription_history_repository(self) -> ISubscriptionHistoryRepository:
        if not self._subscription_history_repo:
            self._subscription_history_repo = PostgresSubscriptionHistoryRepository(self._infra.query_executor)
        return self._subscription_history_repo

    @property
    def push_log_repository(self) -> IPushLogRepository:
        if not self._push_log_repo:
            self._push_log_repo = PostgresPushLogRepository(self._infra.query_executor)
        return self._push_log_repo

    @property
    def user_notification_repository(self) -> IUserNotificationRepository:
        if not self._user_notification_repo:
            self._user_notification_repo = PostgresUserNotificationRepository(self._infra.query_executor)
        return self._user_notification_repo
