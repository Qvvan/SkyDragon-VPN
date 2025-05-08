/**
 * ReferralsScreen.jsx - Экран рефералов
 *
 * Позволяет пользователю приглашать друзей через реферальную программу
 * и отслеживать список приглашенных пользователей.
 */

import React, { useState } from 'react';
import { Star, Users } from 'lucide-react';
import DragonCard from '../components/DragonCard';
import PageHeader from '../components/PageHeader';

const ReferralsScreen = ({ navigateTo }) => {
  const [referralLink, setReferralLink] = useState("t.me/SkyDragonVPN?start=ref123456");
  const [referrals, setReferrals] = useState([
    {
      id: 1,
      name: "Алексей",
      date: "15 апреля 2025",
      status: "invited"
    },
    {
      id: 2,
      name: "Михаил",
      date: "10 апреля 2025",
      status: "paid"
    },
    {
      id: 3,
      name: "Елена",
      date: "5 апреля 2025",
      status: "paid"
    }
  ]);

  const copyReferralLink = () => {
    navigator.clipboard.writeText(referralLink);
    alert("Ссылка скопирована!");
  };

  return (
    <div>
      <PageHeader
        title="Пригласи друга"
        subtitle="Собери армию защитников"
        backButton="home"
        navigateTo={navigateTo}
      />

      <div className="px-4 pb-6">
        <DragonCard className="mb-6 bg-gradient-to-br from-amber-900/20 to-slate-900">
          <div className="flex items-start">
            <div className="w-12 h-12 flex-shrink-0 mr-4">
              <div className="dragon-scroll-icon"></div>
            </div>
            <div>
              <h3 className="text-base font-bold text-amber-500 mb-1">Приглашайте друзей</h3>
              <p className="text-sm text-gray-300">За каждого приглашенного друга, который активирует защиту, вы получите 7 дней защиты дракона Шааргос бесплатно!</p>
            </div>
          </div>

          <div className="mt-4 bg-slate-800/50 rounded-lg p-3 border border-amber-900/20 flex items-center justify-between">
            <p className="text-sm text-gray-300 truncate flex-1">{referralLink}</p>
            <button
              className="text-amber-500 border border-amber-500/30 rounded-md px-3 py-1 text-xs ml-2 hover:bg-amber-500/10 transition-colors flex-shrink-0"
              onClick={copyReferralLink}
            >
              Копировать
            </button>
          </div>

          <div className="mt-4 flex justify-center">
            <button
              className="bg-gradient-to-r from-amber-600 to-red-600 text-white rounded-md px-6 py-2 text-sm hover:from-amber-500 hover:to-red-500 transition-all shadow-md shadow-amber-900/20 flex items-center"
              onClick={() => alert('Поделиться в Telegram')}
            >
              <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1.35 14.05c-.52 0-.45-.2-.64-.65l-1.6-5.26 12.09-7.14"></path>
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm3.38 14.37c-.2.15-.68.15-.87.05-.19-.1-2.81-1.74-3.21-2.04-.4-.3-.67-.5-.35-1.01.32-.51 2.91-2.91 3.12-3.12.21-.21.21-.56-.11-.67-.32-.11-1.24-.46-1.72-.67-.48-.21-.88.26-1.06.47-.18.21-2.33 2.12-2.6 2.35-.27.23-.5.25-.76.05-.26-.2-1.9-1.17-2.92-1.95-1.02-.78-1.54-1.21-1.62-1.74-.08-.53.24-.8.24-.8l1.32-1.3c.36-.36.27-.57.06-.86-.21-.29-2.25-5.9-2.36-6.19-.11-.29-.41-.4-.76-.32-.35.08-2.54.9-2.54.9-1.24.45-1.01 2.25-.67 3.54.34 1.29 1.98 4.59 4.51 7.57 2.53 2.98 5.21 4.26 7.21 4.67 2 .41 2.86-1.03 3.09-1.68.23-.65 1.01-2.54 1.01-2.54.26-.78-.46-.94-.74-.79z"></path>
              </svg>
              Поделиться в Telegram
            </button>
          </div>
        </DragonCard>

        <div className="mb-4">
          <h3 className="text-base font-bold text-gray-300 mb-3 px-1">Ваши приглашения</h3>

          {referrals.length === 0 ? (
            <DragonCard className="text-center py-4">
              <div className="w-12 h-12 bg-slate-700/30 rounded-full flex items-center justify-center mx-auto mb-3">
                <Users className="w-6 h-6 text-gray-500" />
              </div>
              <p className="text-sm text-gray-400">У вас пока нет приглашенных друзей</p>
            </DragonCard>
          ) : (
            <div>
              {referrals.map((referral) => (
                <DragonCard key={referral.id} className="mb-3">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-slate-700 rounded-full flex items-center justify-center mr-3">
                        <span className="text-amber-500 font-bold">{referral.name[0]}</span>
                      </div>
                      <div>
                        <p className="text-base font-medium text-gray-200">{referral.name}</p>
                        <p className="text-xs text-gray-400">Приглашен {referral.date}</p>
                      </div>
                    </div>
                    <div>
                      {referral.status === 'invited' ? (
                        <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded-full border border-blue-500/20">
                          Приглашен
                        </span>
                      ) : (
                        <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full border border-green-500/20">
                          Активировал
                        </span>
                      )}
                    </div>
                  </div>
                </DragonCard>
              ))}

              <div className="mt-4 p-3 bg-amber-500/10 rounded-lg border border-amber-500/20">
                <div className="flex items-center">
                  <div className="mr-3">
                    <Star className="w-5 h-5 text-amber-500" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-200">Ваша награда: <span className="text-amber-500 font-bold">14 дней</span> защиты</p>
                    <p className="text-xs text-gray-400">За 2 активированных приглашения</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReferralsScreen;