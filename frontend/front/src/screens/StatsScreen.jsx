/**
 * StatsScreen.jsx - Экран статистики
 *
 * Отображает информацию о состоянии серверов и общую статистику использования.
 */

import React from 'react';
import DragonCard from '../components/DragonCard';
import PageHeader from '../components/PageHeader';

const StatsScreen = ({ navigateTo }) => {
  const servers = [
    { id: 1, name: "Северный храм", load: 65, ping: 12, status: "online" },
    { id: 2, name: "Долина драконов", load: 38, ping: 24, status: "online" },
    { id: 3, name: "Пустыня теней", load: 91, ping: 45, status: "online" },
    { id: 4, name: "Горный пик", load: 27, ping: 18, status: "online" },
    { id: 5, name: "Забытые руины", load: 0, ping: 0, status: "offline" }
  ];

  return (
    <div>
      <PageHeader
        title="Статистика"
        subtitle="Мощь драконов"
        backButton="home"
        navigateTo={navigateTo}
      />

      <div className="px-4 pb-6">
        <div className="mb-6 grid grid-cols-2 gap-4">
          <DragonCard>
            <div className="text-center">
              <div className="text-2xl font-bold text-amber-500 mb-1">97%</div>
              <p className="text-xs text-gray-400">Серверов онлайн</p>
            </div>
          </DragonCard>

          <DragonCard>
            <div className="text-center">
              <div className="text-2xl font-bold text-amber-500 mb-1">162</div>
              <p className="text-xs text-gray-400">Защищенных</p>
            </div>
          </DragonCard>

          <DragonCard>
            <div className="text-center">
              <div className="text-2xl font-bold text-amber-500 mb-1">99.8%</div>
              <p className="text-xs text-gray-400">Аптайм</p>
            </div>
          </DragonCard>

          <DragonCard>
            <div className="text-center">
              <div className="text-2xl font-bold text-amber-500 mb-1">24/7</div>
              <p className="text-xs text-gray-400">Поддержка</p>
            </div>
          </DragonCard>
        </div>

        <h3 className="text-base font-bold text-gray-300 mb-3 px-1">Статус серверов</h3>

        <div className="space-y-3">
          {servers.map((server) => (
            <DragonCard key={server.id}>
              <div className="flex justify-between items-center">
                <div>
                  <div className="flex items-center">
                    <h4 className="text-base font-bold text-gray-200">{server.name}</h4>
                    {server.status === 'online' ? (
                      <span className="ml-2 w-2 h-2 bg-green-500 rounded-full"></span>
                    ) : (
                      <span className="ml-2 w-2 h-2 bg-red-500 rounded-full"></span>
                    )}
                  </div>
                  {server.status === 'online' && (
                    <p className="text-xs text-gray-400 mt-1">Ping: {server.ping} ms</p>
                  )}
                </div>

                {server.status === 'online' ? (
                  <div className="w-20">
                    <div className="text-xs text-gray-400 mb-1 text-right">Нагрузка: {server.load}%</div>
                    <div className="w-full h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          server.load < 50
                            ? 'bg-green-500'
                            : server.load < 80
                              ? 'bg-amber-500'
                              : 'bg-red-500'
                        }`}
                        style={{ width: `${server.load}%` }}
                      ></div>
                    </div>
                  </div>
                ) : (
                  <span className="text-xs bg-red-500/10 text-red-400 px-2 py-0.5 rounded-full border border-red-500/10">
                    Оффлайн
                  </span>
                )}
              </div>
            </DragonCard>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StatsScreen;