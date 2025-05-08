/**
 * NavButton.jsx - Кнопка для нижней навигации
 *
 * Используется в компоненте BottomNavigation для переключения
 * между основными экранами приложения.
 */

import React from 'react';

const NavButton = ({ icon, label, active, onClick }) => {
  return (
    <button
      className={`flex flex-col items-center justify-center w-16 h-full transition-all ${
        active ? 'text-amber-500' : 'text-gray-400 hover:text-amber-400/80'
      }`}
      onClick={onClick}
    >
      <div className={`transition-transform ${active ? 'scale-110' : ''}`}>
        {icon}
      </div>
      <span className="text-xs mt-1">{label}</span>
      {active && (
        <div className="absolute bottom-0 w-8 h-1 bg-amber-500 rounded-t-lg" />
      )}
    </button>
  );
};

export default NavButton;