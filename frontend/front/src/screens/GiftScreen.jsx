/**
 * GiftScreen.jsx - Экран подарка
 *
 * Позволяет пользователю подарить подписку другому человеку,
 * выбрав подходящий тариф.
 */

import React from 'react';
import DragonCard from '../components/DragonCard';
import PageHeader from '../components/PageHeader';
import services from '../data/services';

const GiftScreen = ({ navigateTo }) => {
  // Используем первые три тарифа для подарков
  const gifts = services.slice(0, 3);

  return (
    <div>
      <PageHeader
        title="Подарить подписку"
        subtitle="Поделись защитой дракона"
        backButton="home"
        navigateTo={navigateTo}
      />

      <div className="px-4 pb-6">
        <DragonCard className="mb-6 bg-gradient-to-br from-slate-800 to-slate-900">
          <div className="flex items-start">
            <div className="w-12 h-12 flex-shrink-0 mr-4">
              <div className="dragon-gift-icon"></div>
            </div>
            <div>
              <h3 className="text-base font-bold text-amber-500 mb-1">Подарить защиту</h3>
              <p className="text-sm text-gray-300">Выберите, какую защиту вы хотите подарить вашему другу. Ссылка на активацию будет отправлена получателю.</p>
            </div>
          </div>
        </DragonCard>

        <h3 className="text-base font-bold text-gray-300 mb-3 px-1">Выберите подарок</h3>

        <div className="space-y-4">
          {gifts.map(gift => (
            <DragonCard
              key={gift.id}
              className={`bg-gradient-to-br ${gift.color} relative overflow-hidden`}
            >
              {gift.popular && (
                <div className="absolute top-0 right-0">
                  <div className="bg-amber-500 text-slate-900 text-xs font-bold py-1 px-4 rounded-bl-lg shadow-md">
                    Популярное
                  </div>
                </div>
              )}

              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-xl font-bold text-amber-500">{gift.name}</h3>
                  <p className="text-sm text-gray-300">{gift.period}</p>
                </div>
                <div className="dragon-icon-wrapper">
                  <div className={`dragon-icon dragon-${gift.name.toLowerCase()}`}></div>
                </div>
              </div>

              <p className="text-sm text-gray-400 mb-3">{gift.description}</p>

              <div className="flex justify-between items-center">
                <div className="text-xl font-bold text-amber-500">{gift.price} ₽</div>
                <button
                  className="bg-gradient-to-r from-amber-600 to-red-600 text-white rounded-md px-4 py-2 text-sm hover:from-amber-500 hover:to-red-500 transition-all shadow-md shadow-amber-900/20"
                  onClick={() => alert(`Подарить: ${gift.name}`)}
                >
                  Подарить
                </button>
              </div>

              <div className="absolute bottom-0 right-0 w-24 h-24 opacity-10">
                <div className={`dragon-watermark dragon-${gift.name.toLowerCase()}-mark`}></div>
              </div>
            </DragonCard>
          ))}
        </div>

        <div className="mt-6">
          <DragonCard>
            <h3 className="text-base font-bold text-gray-200 mb-2">Как это работает?</h3>
            <div className="space-y-2 text-sm text-gray-400">
              <p>1. Выберите дракона, чью защиту хотите подарить</p>
              <p>2. Введите имя и контакт получателя</p>
              <p>3. Оплатите подарок</p>
              <p>4. Получатель получит уникальную ссылку для активации</p>
            </div>
          </DragonCard>
        </div>
      </div>
    </div>
  );
};

export default GiftScreen;