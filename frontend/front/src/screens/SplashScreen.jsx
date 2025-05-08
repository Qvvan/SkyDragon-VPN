/**
 * SplashScreen.jsx - Сплэш-экран при запуске
 *
 * Отображается при загрузке приложения, содержит
 * анимированный логотип и название приложения.
 */

import React from 'react';

const SplashScreen = ({ loaded }) => {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-gradient-to-b from-slate-900 to-slate-800 z-50">
      <div className="flex flex-col items-center">
        <div className={`transition-all duration-1000 ${loaded ? 'scale-100 opacity-100' : 'scale-50 opacity-0'}`}>
          <div className="w-40 h-40 relative">
            <div className="absolute inset-0 dragon-bg-pattern opacity-30"></div>
            <div className="absolute inset-0 dragon-emblem animate-spin-slow"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-16 h-16 dragon-seal"></div>
            </div>
          </div>
        </div>
        <h1 className={`mt-6 text-3xl font-bold text-amber-500 transition-all duration-1000 ${loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          SkyDragon <span className="text-red-500">VPN</span>
        </h1>
        <p className={`mt-2 text-amber-400/70 font-serif italic transition-all duration-1000 delay-300 ${loaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          Древняя защита в цифровом мире
        </p>
      </div>
    </div>
  );
};

export default SplashScreen;