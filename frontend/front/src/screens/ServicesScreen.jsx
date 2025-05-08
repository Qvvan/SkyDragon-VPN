/**
 * ServicesScreen.jsx - Экран услуг
 *
 * Отображает список доступных VPN-услуг с подробным описанием,
 * ценами и возможностью активации.
 */

import React from 'react';
import { Gift } from 'lucide-react';
import DragonCard from '../components/DragonCard';
import PageHeader from '../components/PageHeader';
import services from '../data/services';

const ServicesScreen = ({ navigateTo }) => {
  return (
    <div>
      <PageHeader
        title="Услуги драконов"
        subtitle="Выберите защиту для себя"
        backButton="home"
        navigateTo={navigateTo}
      />

      <div className="px-4 pb-6">
        <div className="flex flex-col space-y-4">
          {services.map(service => (
            <DragonCard
              key={service.id}
              className={`bg-gradient-to-br ${service.color} relative overflow-hidden`}
            >
              {service.popular && (
                <div className="absolute top-0 right-0">
                  <div className="bg-amber-500 text-slate-900 text-xs font-bold py-1 px-4 rounded-bl-lg shadow-md">
                    Популярное
                  </div>
                </div>
              )}

              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-xl font-bold text-amber-500">{service.name}</h3>
                  <p className="text-sm text-gray-300">{service.period}</p>
                </div>
                <div className="dragon-icon-wrapper">
                  <div className={`dragon-icon dragon-${service.name.toLowerCase()}`}></div>
                </div>
              </div>

              <p className="text-sm text-gray-400 italic font-serif mb-3">"{service.dragonPower}"</p>

              <div className="mb-4">
                <ul className="text-sm text-gray-300 space-y-1">
                  {service.features.map((feature, index) => (
                    <li key={index} className="flex items-center">
                      <div className="w-1 h-1 bg-amber-500 rounded-full mr-2"></div>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="flex justify-between items-center">
                <div className="text-xl font-bold text-amber-500">{service.price} ₽</div>
                <button
                  className="bg-gradient-to-r from-amber-600 to-red-600 text-white rounded-md px-4 py-2 text-sm hover:from-amber-500 hover:to-red-500 transition-all shadow-md shadow-amber-900/20"
                  onClick={() => alert(`Оплата подписки: ${service.name}`)}
                >
                  Активировать
                </button>
              </div>

              <div className="absolute bottom-0 right-0 w-24 h-24 opacity-10">
                <div className={`dragon-watermark dragon-${service.name.toLowerCase()}-mark`}></div>
              </div>
            </DragonCard>
          ))}
        </div>

        <div className="mt-8">
          <DragonCard>
            <div className="flex items-center">
              <div className="mr-3">
                <Gift className="w-6 h-6 text-amber-500" />
              </div>
              <div>
                <h3 className="text-base font-bold text-gray-200">Подарить подписку</h3>
                <p className="text-xs text-gray-400">Поделиться силой драконов</p>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-gray-700/30">
              <button
                className="text-sm text-amber-500 hover:text-amber-400 transition-colors flex items-center"
                onClick={() => navigateTo('gift')}
              >
                Выбрать подарок
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </DragonCard>
        </div>

        <div className="mt-4 text-center text-xs text-gray-500">
          <button
            className="text-amber-500/70 hover:text-amber-500 transition-colors"
            onClick={() => navigateTo('terms')}
          >
            Условия оферты
          </button>
        </div>
      </div>
    </div>
  );
};

export default ServicesScreen;