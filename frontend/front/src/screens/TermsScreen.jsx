/**
 * TermsScreen.jsx - Экран условий оферты
 *
 * Отображает публичную оферту и условия использования
 * сервиса SkyDragon VPN.
 */

import React from 'react';
import DragonCard from '../components/DragonCard';
import PageHeader from '../components/PageHeader';

const TermsScreen = ({ navigateTo }) => {
  return (
    <div>
      <PageHeader
        title="Условия оферты"
        subtitle="Драконий свиток законов"
        backButton="services"
        navigateTo={navigateTo}
      />

      <div className="px-4 pb-6">
        <DragonCard className="mb-6">
          <div className="text-center mb-4">
            <div className="w-16 h-16 mx-auto mb-2">
              <div className="dragon-seal-large"></div>
            </div>
            <h3 className="text-lg font-bold text-amber-500">Публичная оферта</h3>
            <p className="text-xs text-gray-400 italic font-serif">Версия от 01 мая 2025 года</p>
          </div>

          <div className="space-y-4 text-sm text-gray-300">
            <p>
              Настоящий документ является публичной офертой ООО "СкайДрагон" (далее — «Исполнитель») и содержит все существенные условия договора на оказание услуг (далее — «Договор»).
            </p>

            <h4 className="text-base font-bold text-amber-500">1. Определения</h4>
            <p>
              1.1. VPN (Virtual Private Network) — технология, обеспечивающая создание логической сети, функционирующей поверх другой сети, например, Интернет.
            </p>
            <p>
              1.2. Пользователь — физическое лицо, принявшее условия настоящей Оферты и использующее услуги, предоставляемые Исполнителем.
            </p>

            <h4 className="text-base font-bold text-amber-500">2. Предмет Договора</h4>
            <p>
              2.1. Исполнитель обязуется предоставить Пользователю услуги виртуальной частной сети (VPN) на условиях, определенных настоящим Договором, а Пользователь обязуется принять и оплатить услуги.
            </p>

            <div className="text-center mt-4">
              <button
                className="text-amber-500 hover:text-amber-400 transition-colors text-sm"
                onClick={() => alert('Открыть полный текст оферты')}
              >
                Читать полный текст
              </button>
            </div>
          </div>
        </DragonCard>

        <DragonCard className="mb-6">
          <h3 className="text-base font-bold text-gray-200 mb-2">Согласие на обработку данных</h3>
          <p className="text-sm text-gray-400 mb-3">
            Пользуясь нашими услугами, вы соглашаетесь с тем, что мы можем собирать и обрабатывать определенные данные в соответствии с нашей Политикой конфиденциальности.
          </p>
          <button
            className="text-sm text-amber-500 flex items-center"
            onClick={() => alert('Открыть политику конфиденциальности')}
          >
            Политика конфиденциальности
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </DragonCard>
      </div>
    </div>
  );
};

export default TermsScreen;