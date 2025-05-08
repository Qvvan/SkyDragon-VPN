/**
 * InstructionsScreen.jsx - Экран инструкций
 *
 * Предоставляет руководство по установке и настройке VPN
 * для разных операционных систем и устройств.
 */

import React, { useState } from 'react';
import { Download } from 'lucide-react';
import DragonCard from '../components/DragonCard';
import PageHeader from '../components/PageHeader';

const InstructionsScreen = ({ navigateTo }) => {
  const [platform, setPlatform] = useState('android');

  const platformGuides = {
    android: [
      "1. Скачайте приложение SkyDragon VPN с нашего официального сайта или из Google Play.",
      "2. Откройте приложение и войдите с помощью своего Telegram аккаунта.",
      "3. Выберите 'Подключиться' и разрешите установку VPN-профиля.",
      "4. Наслаждайтесь безопасным соединением под защитой драконов!"
    ],
    ios: [
      "1. Скачайте приложение SkyDragon VPN из App Store.",
      "2. Откройте приложение и войдите с помощью своего Telegram аккаунта.",
      "3. Выберите 'Подключиться' и подтвердите установку VPN-профиля в настройках.",
      "4. Вернитесь в приложение и активируйте защиту."
    ],
    windows: [
      "1. Скачайте установщик SkyDragon VPN с нашего официального сайта.",
      "2. Запустите установщик и следуйте инструкциям мастера установки.",
      "3. После установки, откройте приложение и войдите с помощью своего Telegram аккаунта.",
      "4. Выберите сервер и нажмите 'Подключиться'."
    ],
    macos: [
      "1. Скачайте установщик SkyDragon VPN с нашего официального сайта.",
      "2. Откройте скачанный .dmg файл и перетащите приложение в папку Applications.",
      "3. Откройте приложение и войдите с помощью своего Telegram аккаунта.",
      "4. При первом подключении, разрешите установку VPN-профиля в системных настройках."
    ]
  };

  return (
    <div>
      <PageHeader
        title="Инструкции"
        subtitle="Свитки драконьей мудрости"
        backButton="home"
        navigateTo={navigateTo}
      />

      <div className="px-4 pb-6">
        <div className="flex mb-4 overflow-x-auto hide-scrollbar">
          <button
            className={`flex-shrink-0 px-4 py-2 rounded-full mr-2 text-sm ${platform === 'android' ? 'bg-amber-500 text-slate-900' : 'bg-slate-800 text-gray-300'}`}
            onClick={() => setPlatform('android')}
          >
            Android
          </button>
          <button
            className={`flex-shrink-0 px-4 py-2 rounded-full mr-2 text-sm ${platform === 'ios' ? 'bg-amber-500 text-slate-900' : 'bg-slate-800 text-gray-300'}`}
            onClick={() => setPlatform('ios')}
          >
            iOS
          </button>
          <button
            className={`flex-shrink-0 px-4 py-2 rounded-full mr-2 text-sm ${platform === 'windows' ? 'bg-amber-500 text-slate-900' : 'bg-slate-800 text-gray-300'}`}
            onClick={() => setPlatform('windows')}
          >
            Windows
          </button>
          <button
            className={`flex-shrink-0 px-4 py-2 rounded-full mr-2 text-sm ${platform === 'macos' ? 'bg-amber-500 text-slate-900' : 'bg-slate-800 text-gray-300'}`}
            onClick={() => setPlatform('macos')}
          >
            macOS
          </button>
        </div>

        <DragonCard className="mb-6 bg-gradient-to-br from-slate-800 to-slate-900">
          <div className="flex items-start mb-4">
            <div className="w-12 h-12 flex-shrink-0 mr-4">
              <div className="dragon-scroll-icon"></div>
            </div>
            <div>
              <h3 className="text-lg font-bold text-amber-500">Установка на {platform.charAt(0).toUpperCase() + platform.slice(1)}</h3>
              <p className="text-xs text-gray-400 italic font-serif">Следуйте указаниям для наилучшей защиты</p>
            </div>
          </div>

          <div className="space-y-4">
            {platformGuides[platform].map((step, index) => (
              <div key={index} className="flex">
                <div className="w-8 h-8 bg-amber-500/10 rounded-full flex items-center justify-center mr-3 flex-shrink-0 border border-amber-500/20">
                  <span className="text-amber-500 font-bold text-sm">{index + 1}</span>
                </div>
                <p className="text-sm text-gray-300 pt-1">{step}</p>
              </div>
            ))}
          </div>

          <div className="mt-6 border-t border-slate-700/30 pt-4">
            <button
              className="bg-gradient-to-r from-amber-600 to-red-600 text-white rounded-md px-6 py-2 text-sm hover:from-amber-500 hover:to-red-500 transition-all shadow-md shadow-amber-900/20 w-full flex items-center justify-center"
              onClick={() => alert('Загрузка приложения')}
            >
              <Download className="w-4 h-4 mr-2" />
              Скачать для {platform.charAt(0).toUpperCase() + platform.slice(1)}
            </button>
          </div>
        </DragonCard>

        <h3 className="text-base font-bold text-gray-300 mb-3 px-1">Дополнительные инструкции</h3>

        <DragonCard className="mb-3">
          <h4 className="text-base font-bold text-gray-200 mb-2">Диагностика соединения</h4>
          <p className="text-sm text-gray-400 mb-3">
            Если у вас возникли проблемы с подключением, следуйте этим шагам, чтобы диагностировать и решить проблему.
          </p>
          <button
            className="text-sm text-amber-500 flex items-center"
            onClick={() => alert('Открыть раздел диагностики')}
          >
            Подробнее
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </DragonCard>

        <DragonCard className="mb-3">
          <h4 className="text-base font-bold text-gray-200 mb-2">Настройка маршрутизации</h4>
          <p className="text-sm text-gray-400 mb-3">
            Продвинутые настройки для опытных пользователей, позволяющие настроить правила маршрутизации трафика.
          </p>
          <button
            className="text-sm text-amber-500 flex items-center"
            onClick={() => alert('Открыть настройки маршрутизации')}
          >
            Подробнее
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </DragonCard>
      </div>
    </div>
  );
};

export default InstructionsScreen;