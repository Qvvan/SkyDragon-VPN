/**
 * HomeScreen.jsx - Главный экран приложения
 *
 * Отображает текущий статус подписки и основные функции приложения.
 */

import React, { useState } from 'react';
import { Star, Shield, Users, Download, Gift, Activity, Clock, RefreshCw } from 'lucide-react';
import DragonCard from '../components/DragonCard';

const HomeScreen = ({ navigateTo }) => {
  const [activeSubscription, setActiveSubscription] = useState({
    name: "Валдрим",
    days: 28,
    type: "Месячная защита",
    status: "active",
    expires: "28 мая 2025",
    progress: 70
  });

  return (
    <div className="flex flex-col min-h-full">
      <div className="px-4 pt-6 pb-3 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-500">SkyDragon VPN</h1>
          <p className="text-sm text-amber-400/70 font-serif italic">Древняя защита в цифровом мире</p>
        </div>
        <div className="w-16 h-16 dragon-emblem animate-spin-slow"></div>
      </div>

      <div className="px-4 py-2">
        {activeSubscription && (
          <DragonCard className="mb-6 bg-gradient-to-br from-amber-900/20 to-slate-900">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="text-lg font-bold text-amber-500">Подписка активна</h3>
                <p className="text-sm text-gray-300">Защита дракона {activeSubscription.name}</p>
              </div>
              <div className="relative">
                <div className="dragon-seal w-12 h-12 animate-pulse-slow"></div>
              </div>
            </div>

            <div className="mt-4">
              <div className="flex justify-between items-center text-sm mb-1">
                <span className="text-gray-400">Осталось {activeSubscription.days} дней</span>
                <span className="text-gray-400">до {activeSubscription.expires}</span>
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
                onClick={() => navigateTo('subscriptions')}
              >
                <Clock className="w-4 h-4 mr-1" />
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
        )}

        {!activeSubscription && (
          <DragonCard className="mb-6 bg-gradient-to-br from-slate-800/50 to-slate-900 border-dashed">
            <div className="flex flex-col items-center py-4">
              <div className="w-16 h-16 bg-slate-700/30 rounded-full flex items-center justify-center mb-4">
                <Shield className="w-8 h-8 text-gray-500" />
              </div>
              <h3 className="text-lg font-bold text-amber-400 mb-1">Нет активной защиты</h3>
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

        <div className="grid grid-cols-2 gap-4 mb-6">
          <DragonCard
            className="cursor-pointer hover:border-amber-500/30 transition-colors"
            onClick={() => navigateTo('services')}
          >
            <div className="flex flex-col items-center text-center h-24 justify-center">
              <div className="text-amber-500 mb-2">
                <Star className="w-8 h-8" />
              </div>
              <h3 className="text-sm font-bold text-gray-200">Услуги драконов</h3>
              <p className="text-xs text-gray-400 mt-1">Выбрать защиту</p>
            </div>
          </DragonCard>

          <DragonCard
            className="cursor-pointer hover:border-amber-500/30 transition-colors"
            onClick={() => navigateTo('referrals')}
          >
            <div className="flex flex-col items-center text-center h-24 justify-center">
              <div className="text-amber-500 mb-2">
                <Users className="w-8 h-8" />
              </div>
              <h3 className="text-sm font-bold text-gray-200">Пригласить друга</h3>
              <p className="text-xs text-gray-400 mt-1">Получить награду</p>
            </div>
          </DragonCard>

          <DragonCard
            className="cursor-pointer hover:border-amber-500/30 transition-colors"
            onClick={() => navigateTo('instructions')}
          >
            <div className="flex flex-col items-center text-center h-24 justify-center">
              <div className="text-amber-500 mb-2">
                <Download className="w-8 h-8" />
              </div>
              <h3 className="text-sm font-bold text-gray-200">Инструкции</h3>
              <p className="text-xs text-gray-400 mt-1">Как настроить</p>
            </div>
          </DragonCard>

          <DragonCard
            className="cursor-pointer hover:border-amber-500/30 transition-colors"
            onClick={() => navigateTo('gift')}
          >
            <div className="flex flex-col items-center text-center h-24 justify-center">
              <div className="text-amber-500 mb-2">
                <Gift className="w-8 h-8" />
              </div>
              <h3 className="text-sm font-bold text-gray-200">Подарить</h3>
              <p className="text-xs text-gray-400 mt-1">Защиту другу</p>
            </div>
          </DragonCard>
        </div>

        <DragonCard className="mb-6">
          <div className="flex items-center">
            <div className="mr-4">
              <Activity className="w-8 h-8 text-amber-500" />
            </div>
            <div className="flex-1">
              <h3 className="text-base font-bold text-gray-200">Статистика драконов</h3>
              <div className="flex justify-between mt-2">
                <div className="text-center">
                  <p className="text-amber-500 text-lg font-bold">97%</p>
                  <p className="text-xs text-gray-400">Сервера онлайн</p>
                </div>
                <div className="text-center">
                  <p className="text-amber-500 text-lg font-bold">162</p>
                  <p className="text-xs text-gray-400">Защищенных</p>
                </div>
                <div className="text-center">
                  <p className="text-amber-500 text-lg font-bold">12ms</p>
                  <p className="text-xs text-gray-400">Ping</p>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-gray-700/30">
            <button
              className="text-sm text-amber-500 hover:text-amber-400 transition-colors flex items-center"
              onClick={() => navigateTo('stats')}
            >
              Подробная статистика
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </DragonCard>
      </div>
    </div>
  );
};

export default HomeScreen;