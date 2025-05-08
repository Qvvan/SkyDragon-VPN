/**
 * PageHeader.jsx - Компонент заголовка страницы
 *
 * Используется для отображения заголовка и кнопки "назад"
 * в верхней части экрана.
 */

import React from 'react';

const PageHeader = ({ title, subtitle, backButton, navigateTo, action }) => {
  return (
    <div className="sticky top-0 z-20 pt-3 pb-2 px-4 bg-gradient-to-b from-slate-900 to-slate-900/90 backdrop-blur-md border-b border-amber-900/30 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          {backButton && (
            <button
              className="mr-3 p-1 text-amber-500/70 hover:text-amber-500 transition-colors"
              onClick={() => navigateTo(backButton)}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          )}
          <div>
            <h1 className="text-xl font-bold text-amber-500">{title}</h1>
            {subtitle && (
              <p className="text-xs text-amber-400/70 font-serif italic">{subtitle}</p>
            )}
          </div>
        </div>
        {action && (
          <div>{action}</div>
        )}
      </div>
    </div>
  );
};

export default PageHeader;