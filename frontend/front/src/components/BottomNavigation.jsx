/**
 * BottomNavigation.jsx - Компонент нижней навигации
 *
 * Отображает панель навигации внизу экрана для быстрого
 * переключения между основными разделами приложения.
 */

import React from 'react';
import { Shield, Clock, Star, Users, Settings } from 'lucide-react';
import NavButton from './NavButton';

const BottomNavigation = ({ activeScreen, navigateTo }) => {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-slate-900 to-slate-900/80 backdrop-blur-md border-t border-amber-900/30">
      <div className="flex justify-around items-center h-16 px-2 max-w-md mx-auto">
        <NavButton
          icon={<Shield className="w-5 h-5" />}
          label="Главная"
          active={activeScreen === 'home'}
          onClick={() => navigateTo('home')}
        />
        <NavButton
          icon={<Clock className="w-5 h-5" />}
          label="Подписки"
          active={activeScreen === 'subscriptions'}
          onClick={() => navigateTo('subscriptions')}
        />
        <NavButton
          icon={<Star className="w-5 h-5" />}
          label="Услуги"
          active={activeScreen === 'services'}
          onClick={() => navigateTo('services')}
        />
        <NavButton
          icon={<Users className="w-5 h-5" />}
          label="Друзья"
          active={activeScreen === 'referrals'}
          onClick={() => navigateTo('referrals')}
        />
        <NavButton
          icon={<Settings className="w-5 h-5" />}
          label="Ещё"
          active={activeScreen === 'support'}
          onClick={() => navigateTo('support')}
        />
      </div>
    </div>
  );
};

export default BottomNavigation;