/**
 * PaymentHistoryScreen.jsx - Экран истории платежей
 *
 * Отображает список всех платежей пользователя с датами,
 * суммами и статусами транзакций.
 */

import React from 'react';
import { CreditCard } from 'lucide-react';
import DragonCard from '../components/DragonCard';
import PageHeader from '../components/PageHeader';

const PaymentHistoryScreen = ({ navigateTo }) => {
  const payments = [
    {
      id: 1,
      date: "28 апреля 2025",
      service: "Валдрим (1 месяц)",
      amount: 300,
      status: "success"
    },
    {
      id: 2,
      date: "1 апреля 2025",
      service: "Шааргос (1 неделя)",
      amount: 100,
      status: "success"
    },
    {
      id: 3,
      date: "15 марта 2025",
      service: "Подарок другу - Шааргос",
      amount: 100,
      status: "success"
    }
  ];

  return (
    <div>
      <PageHeader
        title="История платежей"
        subtitle="Финансовая хроника"
        backButton="subscriptions"
        navigateTo={navigateTo}
      />

      <div className="px-4 pb-6">
        {payments.length === 0 ? (
          <DragonCard className="text-center py-6">
            <div className="w-16 h-16 bg-slate-700/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <CreditCard className="w-8 h-8 text-gray-500" />
            </div>
            <h3 className="text-base font-bold text-gray-300 mb-1">Нет платежей</h3>
            <p className="text-sm text-gray-400">Ваша финансовая хроника пуста</p>
          </DragonCard>
        ) : (
          <div>
            {payments.map((payment) => (
              <DragonCard key={payment.id} className="mb-3">
                <div className="flex justify-between">
                  <div>
                    <p className="text-base font-medium text-gray-200">{payment.service}</p>
                    <p className="text-xs text-gray-400">{payment.date}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-base font-bold text-amber-500">{payment.amount} ₽</p>
                    <p className={`text-xs ${payment.status === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                      {payment.status === 'success' ? 'Успешно' : 'Ошибка'}
                    </p>
                  </div>
                </div>
              </DragonCard>
            ))}

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-400">Показаны последние {payments.length} платежей</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PaymentHistoryScreen;