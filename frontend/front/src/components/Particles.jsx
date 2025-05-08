/**
 * Particles.jsx - Анимированные частицы фона
 *
 * Создает эффект плавающих частиц в фоне приложения
 * для более динамичного и атмосферного интерфейса.
 */

import React from 'react';

const Particles = () => {
  return (
    <div className="particles-container absolute inset-0 z-0">
      {[...Array(20)].map((_, i) => (
        <div
          key={i}
          className="particle absolute rounded-full bg-amber-500/20"
          style={{
            width: `${Math.random() * 10 + 2}px`,
            height: `${Math.random() * 10 + 2}px`,
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
            animationDuration: `${Math.random() * 20 + 10}s`,
            animationDelay: `${Math.random() * 5}s`
          }}
        ></div>
      ))}
    </div>
  );
};

export default Particles;