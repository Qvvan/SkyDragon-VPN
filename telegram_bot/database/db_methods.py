from database.methods import services, users, subscriptions, server, pushes, subscription_history, \
    referrals, payments, gifts, keys, notifications


class MethodsManager:
    def __init__(self, session):
        self.session = session

        self.users = users.UserMethods(self.session)
        self.subscription = subscriptions.SubscriptionMethods(self.session)
        self.services = services.ServiceMethods(self.session)
        self.servers = server.ServerMethods(self.session)
        self.pushes = pushes.PushesMethods(self.session)
        self.subscription_history = subscription_history.SubscriptionsHistoryMethods(self.session)
        self.referrals = referrals.ReferralMethods(self.session)
        self.payments = payments.PaymentsMethods(self.session)
        self.gifts = gifts.GiftsMethods(self.session)
        self.keys = keys.KeysMethods(self.session)
        self.notifications = notifications.NotificationMethods(self.session)
