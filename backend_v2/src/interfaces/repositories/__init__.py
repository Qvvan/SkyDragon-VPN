from src.interfaces.repositories.account import IAccountRepository
from src.interfaces.repositories.account_telegram_link import IAccountTelegramLinkRepository
from src.interfaces.repositories.payment import IPaymentRepository
from src.interfaces.repositories.server import IServerRepository
from src.interfaces.repositories.service_plan import IServicePlanRepository
from src.interfaces.repositories.subscription import ISubscriptionRepository
from src.interfaces.repositories.subscription_provision_task import ISubscriptionProvisionTaskRepository

__all__ = [
    "IAccountRepository",
    "IAccountTelegramLinkRepository",
    "IPaymentRepository",
    "IServerRepository",
    "IServicePlanRepository",
    "ISubscriptionRepository",
    "ISubscriptionProvisionTaskRepository",
]
