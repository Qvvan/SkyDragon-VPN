/**
 * DragonCard.jsx - Стилизованная карточка с драконьим орнаментом
 *
 * Переиспользуемый компонент для создания карточек в стиле приложения.
 */

import React from 'react';

const DragonCard = ({ children, className = '', onClick }) => {
  return (
    <div
      className={`relative bg-gradient-to-br from-slate-800 to-slate-900 border border-amber-900/30 rounded-lg p-4 shadow-lg overflow-hidden ${className}`}
      onClick={onClick}
    >
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-900/0 via-amber-500/40 to-amber-900/0"></div>
      <div className="absolute top-0 right-0 w-8 h-8 dragon-corner-ornament"></div>
      <div className="absolute bottom-0 left-0 w-8 h-8 dragon-corner-ornament transform rotate-180"></div>
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};

export default DragonCard;