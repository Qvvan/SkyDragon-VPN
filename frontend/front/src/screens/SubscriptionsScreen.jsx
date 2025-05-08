/**
 * SubscriptionsScreen.jsx - Экран подписок
 *
 * Отображает активные и истекшие подписки пользователя,
 * а также позволяет управлять автопродлением.
 */

import React, { useState } from 'react';
import { HelpCircle, RefreshCw, Clock, CreditCard, Shield } from 'lucide-react';
import DragonCard from '../components/DragonCard';
import PageHeader from '../components/PageHeader';

const SubscriptionsScreen = ({ navigateTo }) => {
  const [activeSubscription, setActiveSubscription] = useState({
    id: 1,
    name: "Валдрим",
    startDate: "28 апреля 2025",
    endDate: "28 мая 2025",
    status: "active",
    autoRenewal: true,
    devices: 3,
    progress: 70
  });

  const [expiredSubscriptions, setExpiredSubscriptions] = useState([
    {
      id: 2,
      name: "Шааргос",
      startDate: "1 апреля 2025",
      endDate: "7 апреля 2025",
      status: "expired",
      autoRenewal: false
    }
  ]);

  const toggleAutoRenewal = () => {
    setActiveSubscription({
      ...activeSubscription,
      autoRenewal: !activeSubscription.autoRenewal
    });
  };

  return (
    <div>
      <PageHeader
        title="Мои подписки"
        subtitle="Управление защитой"
        backButton="home"
        navigateTo={navigateTo}
      />

      <div className="px-4 pb-6">
        {activeSubscription ? (
          <DragonCard className="mb-6 bg-gradient-to-br from-amber-900/20 to-slate-900">
            <div className="flex justify-between items-start mb-3">
              <div>
                <div className="flex items-center">
                  <h3 className="text-lg font-bold text-amber-500">Дракон {activeSubscription.name}</h3>
                  <span className="ml-2 text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full border border-green-500/20">
                    Активна
                  </span>
                </div>
                <p className="text-sm text-gray-300 mt-1">Месячная защита</p>
              </div>
              <div className="relative">
                <div className={`dragon-icon-small dragon-${activeSubscription.name.toLowerCase()}`}></div>
              </div>
            </div>

            <div className="mt-3 bg-slate-800/30 rounded-lg p-3 border border-amber-900/10">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-gray-400">Начало защиты</p>
                  <p className="text-gray-200">{activeSubscription.startDate}</p>
                </div>
                <div>
                  <p className="text-gray-400">Конец защиты</p>
                  <p className="text-gray-200">{activeSubscription.endDate}</p>
                </div>
                <div>
                  <p className="text-gray-400">Устройства</p>
                  <p className="text-gray-200">{activeSubscription.devices} из 3</p>
                </div>
                <div>
                  <p className="text-gray-400">Автопродление</p>
                  <p className="text-gray-200 flex items-center">
                    {activeSubscription.autoRenewal ? 'Включено' : 'Выключено'}
                    <span className={`ml-2 w-8 h-4 rounded-full flex items-center transition-colors duration-300 ${activeSubscription.autoRenewal ? 'bg-amber-500' : 'bg-gray-600'}`} onClick={toggleAutoRenewal}>
                      <span className={`w-3 h-3 rounded-full bg-white transform transition-transform duration-300 ${activeSubscription.autoRenewal ? 'translate-x-4' : 'translate-x-1'}`}></span>
                    </span>
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-4">
              <div className="flex justify-between items-center text-sm mb-1">
                <span className="text-gray-400">Осталось 30%</span>
                <span className="text-gray-400">{Math.round(30 * activeSubscription.devices / 100)} дней</span>
              </div>
              <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber-500 to-red-500 rounded-full"
                  style={{ width: `${activeSubscription.progress}%` }}
                ></div>
              </div>
            </div>

            <div className="mt-4 flex justify-between">
              <button
                className="text-amber-500 border border-amber-500/30 rounded-md px-4 py-1 text-sm hover:bg-amber-500/10 transition-colors flex items-center"
                onClick={() => alert('Информация о подписке')}
              >
                <HelpCircle className="w-4 h-4 mr-1" />
                Подробнее
              </button>
              <button
                className="bg-gradient-to-r from-amber-600 to-red-600 text-white rounded-md px-4 py-1 text-sm hover:from-amber-500 hover:to-red-500 transition-all shadow-md shadow-amber-900/20 flex items-center"
                onClick={() => navigateTo('services')}
              >
                <RefreshCw className="w-4 h-4 mr-1" />
                Продлить
              </button>
            </div>
          </DragonCard>
        ) : (
          <DragonCard className="mb-6 bg-gradient-to-br from-slate-800/50 to-slate-900 border-dashed">
            <div className="flex flex-col items-center py-4">
              <div className="w-16 h-16 bg-slate-700/30 rounded-full flex items-center justify-center mb-4">
                <Shield className="w-8 h-8 text-gray-500" />
              </div>
              <h3 className="text-lg font-bold text-amber-400 mb-1">Нет активных подписок</h3>
              <p className="text-sm text-gray-400 text-center mb-4">Активируйте защиту драконов для безопасного соединения</p>
              <button
                className="bg-gradient-to-r from-amber-600 to-red-600 text-white rounded-md px-6 py-2 text-sm hover:from-amber-500 hover:to-red-500 transition-all shadow-md shadow-amber-900/20"
                onClick={() => navigateTo('services')}
              >
                Выбрать защиту
              </button>
            </div>
          </DragonCard>
        )}

        {expiredSubscriptions.length > 0 && (
          <div className="mb-4">
            <h3 className="text-base font-bold text-gray-300 mb-3 px-1">История подписок</h3>

            {expiredSubscriptions.map((sub) => (
              <DragonCard key={sub.id} className="mb-3 bg-gradient-to-br from-slate-800 to-slate-900">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center">
                      <h3 className="text-base font-bold text-gray-300">Дракон {sub.name}</h3>
                      <span className="ml-2 text-xs bg-red-500/10 text-red-400 px-2 py-0.5 rounded-full border border-red-500/10">
                        Истекла
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {sub.startDate} — {sub.endDate}
                    </p>
                  </div>
                  <button
                    className="text-amber-500 border border-amber-500/30 rounded-md px-3 py-1 text-xs hover:bg-amber-500/10 transition-colors"
                    onClick={() => navigateTo('services')}
                  >
                    Возобновить
                  </button>
                </div>
              </DragonCard>
            ))}
          </div>
        )}

        <div className="mt-6">
          <DragonCard className="text-center py-3">
            <button
              className="text-amber-500 hover:text-amber-400 transition-colors flex items-center justify-center mx-auto"
              onClick={() => navigateTo('payment-history')}
            >
              <CreditCard className="w-4 h-4 mr-2" />
              История платежей
            </button>
          </DragonCard>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionsScreen;