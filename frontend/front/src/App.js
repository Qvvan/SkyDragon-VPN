/**
 * App.jsx - Корневой компонент приложения SkyDragon VPN
 *
 * Этот компонент управляет навигацией между экранами
 * и содержит основную структуру интерфейса.
 */

import React, { useState, useEffect } from 'react';
import { Shield } from 'lucide-react';

// Импорт стилей
import './styles/globals.css';
import './styles/animations.css';
import './styles/dragonIcons.css';

// Импорт компонентов
import BottomNavigation from './components/BottomNavigation';
import Particles from './components/Particles';

// Импорт экранов
import SplashScreen from './screens/SplashScreen';
import HomeScreen from './screens/HomeScreen';
import ServicesScreen from './screens/ServicesScreen';
import SubscriptionsScreen from './screens/SubscriptionsScreen';
import PaymentHistoryScreen from './screens/PaymentHistoryScreen';
import ReferralsScreen from './screens/ReferralsScreen';
import SupportScreen from './screens/SupportScreen';
import StatsScreen from './screens/StatsScreen';
import InstructionsScreen from './screens/InstructionsScreen';
import TermsScreen from './screens/TermsScreen';
import GiftScreen from './screens/GiftScreen';

// Главный компонент приложения
const App = () => {
  const [activeScreen, setActiveScreen] = useState('home');
  const [loaded, setLoaded] = useState(false);
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    // Имитация загрузки и отображение сплэш-экрана
    setTimeout(() => {
      setLoaded(true);
    }, 500);

    setTimeout(() => {
      setShowSplash(false);
    }, 2500);
  }, []);

  // Переключение между экранами
  const navigateTo = (screen) => {
    setActiveScreen(screen);
  };

  // Если показываем сплэш-экран при запуске
  if (showSplash) {
    return <SplashScreen loaded={loaded} />;
  }

  // Определяем, какой экран отображать
  const renderScreen = () => {
    switch(activeScreen) {
      case 'home':
        return <HomeScreen navigateTo={navigateTo} />;
      case 'services':
        return <ServicesScreen navigateTo={navigateTo} />;
      case 'subscriptions':
        return <SubscriptionsScreen navigateTo={navigateTo} />;
      case 'payment-history':
        return <PaymentHistoryScreen navigateTo={navigateTo} />;
      case 'referrals':
        return <ReferralsScreen navigateTo={navigateTo} />;
      case 'support':
        return <SupportScreen navigateTo={navigateTo} />;
      case 'stats':
        return <StatsScreen navigateTo={navigateTo} />;
      case 'instructions':
        return <InstructionsScreen navigateTo={navigateTo} />;
      case 'terms':
        return <TermsScreen navigateTo={navigateTo} />;
      case 'gift':
        return <GiftScreen navigateTo={navigateTo} />;
      default:
        return <HomeScreen navigateTo={navigateTo} />;
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 text-gray-100 relative overflow-hidden">
      {/* Фон с драконами и анимированными эффектами */}
      <div className="absolute inset-0 overflow-hidden z-0 opacity-20">
        <div className="dragon-bg-pattern"></div>
        <div className="absolute top-0 left-0 w-full h-full bg-dragon-texture"></div>
      </div>

      {/* Анимированные частицы */}
      <Particles />

      {/* Основной контент */}
      <div className="relative z-10 flex-1 overflow-auto pb-16">
        {renderScreen()}
      </div>

      {/* Нижняя навигация */}
      <BottomNavigation activeScreen={activeScreen} navigateTo={navigateTo} />
    </div>
  );
};

export default App;