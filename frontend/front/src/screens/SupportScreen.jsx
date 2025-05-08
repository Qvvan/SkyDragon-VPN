/**
 * SupportScreen.jsx - Экран технической поддержки
 *
 * Отображает часто задаваемые вопросы и предоставляет
 * возможность обратиться в техническую поддержку.
 */

import React from 'react';
import { HelpCircle } from 'lucide-react';
import DragonCard from '../components/DragonCard';
import PageHeader from '../components/PageHeader';

const SupportScreen = ({ navigateTo }) => {
  const faqs = [
    {
      id: 1,
      question: "Как настроить VPN на устройстве?",
      answer: "Для настройки SkyDragon VPN вам потребуется скачать приложение на ваше устройство и следовать инструкциям. Подробная инструкция доступна в разделе 'Инструкции'."
    },
    {
      id: 2,
      question: "Как отменить автопродление?",
      answer: "Вы можете отключить автопродление в разделе 'Подписки', выбрав активную подписку и переключив соответствующий тумблер."
    },
    {
      id: 3,
      question: "Как работает реферальная система?",
      answer: "За каждого приглашенного друга, который активирует защиту дракона, вы получаете 7 дней защиты дракона Шааргос. Ваш друг также получает 3 дня бесплатной защиты."
    },
    {
      id: 4,
      question: "Сколько устройств можно защитить?",
      answer: "Число устройств зависит от выбранного дракона-защитника: Шааргос - 1 устройство, Валдрим - 3 устройства, Сангрил - 5 устройств, Элдрагон - без ограничений."
    }
  ];

  return (
    <div>
      <PageHeader
        title="Поддержка"
        subtitle="Мудрость драконов"
        backButton="home"
        navigateTo={navigateTo}
      />

      <div className="px-4 pb-6">
        <DragonCard className="mb-6">
          <div className="flex items-center mb-4">
            <div className="mr-3">
              <HelpCircle className="w-6 h-6 text-amber-500" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-200">Нужна помощь?</h3>
              <p className="text-xs text-gray-400">Наши драконы готовы помочь</p>
            </div>
          </div>

          <button
            className="w-full bg-gradient-to-r from-amber-600 to-red-600 text-white rounded-md py-2 text-sm hover:from-amber-500 hover:to-red-500 transition-all shadow-md shadow-amber-900/20 flex items-center justify-center"
            onClick={() => alert('Открыть чат с поддержкой')}
          >
            <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1.35 14.05c-.52 0-.45-.2-.64-.65l-1.6-5.26 12.09-7.14"></path>
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm3.38 14.37c-.2.15-.68.15-.87.05-.19-.1-2.81-1.74-3.21-2.04-.4-.3-.67-.5-.35-1.01.32-.51 2.91-2.91 3.12-3.12.21-.21.21-.56-.11-.67-.32-.11-1.24-.46-1.72-.67-.48-.21-.88.26-1.06.47-.18.21-2.33 2.12-2.6 2.35-.27.23-.5.25-.76.05-.26-.2-1.9-1.17-2.92-1.95-1.02-.78-1.54-1.21-1.62-1.74-.08-.53.24-.8.24-.8l1.32-1.3c.36-.36.27-.57.06-.86-.21-.29-2.25-5.9-2.36-6.19-.11-.29-.41-.4-.76-.32-.35.08-2.54.9-2.54.9-1.24.45-1.01 2.25-.67 3.54.34 1.29 1.98 4.59 4.51 7.57 2.53 2.98 5.21 4.26 7.21 4.67 2 .41 2.86-1.03 3.09-1.68.23-.65 1.01-2.54 1.01-2.54.26-.78-.46-.94-.74-.79z"></path>
            </svg>
            Написать в поддержку
          </button>
        </DragonCard>

        <h3 className="text-lg font-bold text-amber-500 mb-4 px-1">Часто задаваемые вопросы</h3>

        <div className="space-y-3">
          {faqs.map((faq) => (
            <DragonCard key={faq.id}>
              <div className="mb-2">
                <h4 className="text-base font-bold text-gray-200">{faq.question}</h4>
              </div>
              <p className="text-sm text-gray-400">{faq.answer}</p>
            </DragonCard>
          ))}
        </div>

        <div className="mt-6 text-center">
          <button
            className="text-sm text-amber-500 hover:text-amber-400 transition-colors"
            onClick={() => navigateTo('instructions')}
          >
            Перейти к инструкциям по установке
          </button>
        </div>
      </div>
    </div>
  );
};

export default SupportScreen;