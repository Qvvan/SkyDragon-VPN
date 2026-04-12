import { useState } from 'react'
import { motion } from 'framer-motion'
import { Button } from '../../components/ui/Button'
import { Modal } from '../../components/ui/Modal'
import { Skeleton } from '../../components/ui/Skeleton'
import { useReferralStats, useReferralList, useCreateGift } from '../../hooks/useReferrals'
import { useServices } from '../../hooks/useServices'
import { useUIStore } from '../../stores/ui.store'
import type { GiftCode } from '../../types/gift.types'

export function ReferralsContent() {
  const { data: stats, isLoading: loadingStats } = useReferralStats()
  const { data: referrals, isLoading: loadingReferrals } = useReferralList()
  const { data: services } = useServices()
  const createGift = useCreateGift()
  const { addToast } = useUIStore()

  const [giftOpen, setGiftOpen] = useState(false)
  const [giftServiceId, setGiftServiceId] = useState('')
  const [createdGift, setCreatedGift] = useState<GiftCode | null>(null)
  const selectedService = services?.find((svc) => svc.id === giftServiceId)

  function copyLink() {
    if (!stats?.referralLink) return
    navigator.clipboard.writeText(stats.referralLink)
    addToast('Реферальная ссылка скопирована!')
  }

  function copyGiftCode() {
    if (!createdGift) return
    navigator.clipboard.writeText(createdGift.code)
    addToast('Код подарка скопирован!')
  }

  async function handleCreateGift() {
    if (!giftServiceId || !selectedService) return
    try {
      const gift = await createGift.mutateAsync({ serviceId: giftServiceId, durationDays: selectedService.durationDays })
      setCreatedGift(gift)
    } catch {
      addToast('Ошибка создания подарка.', 'error')
    }
  }

  function openGiftModal() {
    setCreatedGift(null)
    setGiftServiceId(services?.[0]?.id ?? '')
    setGiftOpen(true)
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
      className="space-y-5"
    >
      {/* Referral link */}
      <motion.div variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }} transition={{ duration: 0.4, ease: 'easeOut' }}>
        <p className="font-mono text-xs text-text-faint uppercase tracking-wider mb-2">Ваша ссылка</p>
        {loadingStats ? (
          <Skeleton className="h-10 w-full" />
        ) : (
          <div className="flex items-center gap-2">
            <div className="flex-1 rounded-xl px-4 py-3 bg-surface-3 font-mono text-sm text-text-dim truncate shadow-card">
              {stats?.referralLink}
            </div>
            <Button size="md" variant="primary" onClick={copyLink}>Копировать</Button>
          </div>
        )}
      </motion.div>

      {/* Stats */}
      <motion.div
        variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="grid grid-cols-2 gap-4"
      >
        {loadingStats ? (
          <><Skeleton className="h-16" /><Skeleton className="h-16" /></>
        ) : (
          <>
            <div className="rounded-2xl p-5 bg-surface-3 shadow-card">
              <p className="font-mono text-3xl sm:text-4xl text-jade tabular-nums">{stats?.totalReferrals ?? 0}</p>
              <p className="font-mono text-sm text-text-dim mt-1.5">Приведено друзей</p>
            </div>
            <div className="rounded-2xl p-5 bg-surface-3 shadow-card">
              <p className="font-mono text-3xl sm:text-4xl text-jade tabular-nums">{stats?.totalBonusDays ?? 0}</p>
              <p className="font-mono text-sm text-text-dim mt-1.5">Бонусных дней</p>
            </div>
          </>
        )}
      </motion.div>

      {/* Info note */}
      <motion.div variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }} transition={{ duration: 0.4, ease: 'easeOut' }}>
        <div className="rounded-xl px-3 py-2.5 bg-jade-dim shadow-[0_0_0_1px_rgba(157,140,255,0.18)]">
          <div className="flex items-start gap-2">
            <ReferralIcon />
            <p className="font-mono text-sm text-jade leading-relaxed">
              За каждого приглашённого друга вы получаете +15 дней к подписке
            </p>
          </div>
        </div>
      </motion.div>

      {/* Create gift */}
      <motion.div variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }} transition={{ duration: 0.4, ease: 'easeOut' }}>
        <Button variant="ghost" className="w-full" onClick={openGiftModal}>
          <span className="inline-flex items-center gap-2">
            <GiftIcon />
            Создать подарочную подписку
          </span>
        </Button>
      </motion.div>

      {/* Referral list */}
      {loadingReferrals ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10" />)}
        </div>
      ) : referrals?.length ? (
        <motion.div variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }} transition={{ duration: 0.4, ease: 'easeOut' }}>
          <p className="font-mono text-xs text-text-faint uppercase tracking-wider mb-3">Приглашённые друзья</p>
          <div className="space-y-2">
            {referrals.map((ref) => (
              <div key={ref.id} className="flex items-center justify-between py-3.5 px-4 rounded-2xl bg-surface-3">
                <span className="font-mono text-sm sm:text-base text-text">{ref.maskedPhone}</span>
                <div className="flex items-center gap-3 sm:gap-4">
                  <span className="font-mono text-xs sm:text-sm text-text-dim tabular-nums">
                    {new Date(ref.joinedAt).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}
                  </span>
                  <span className="font-mono text-sm text-jade tabular-nums font-medium">+{ref.bonusDaysGranted} дн.</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      ) : (
        <p className="font-mono text-sm text-text-dim text-center py-8">
          Друзей пока нет. Поделитесь ссылкой!
        </p>
      )}

      {/* Gift modal */}
      <Modal open={giftOpen} onClose={() => setGiftOpen(false)} title="Создать подарок">
        {createdGift ? (
          <div className="px-6 sm:px-7 pb-7 pt-5 space-y-5">
            <div className="text-center py-3">
              <div className="mb-4 inline-flex items-center justify-center size-16 rounded-2xl"
                style={{ background: 'rgba(157,140,255,0.08)', border: '1px solid rgba(157,140,255,0.18)' }}>
                <GiftIcon large />
              </div>
              <p className="font-display text-2xl sm:text-3xl text-text mb-2">Подарок создан!</p>
              <p className="font-mono text-sm sm:text-base text-text-dim text-pretty leading-relaxed">
                Поделитесь кодом —{' '}
                <span className="text-jade tabular-nums">{createdGift.durationDays} дней</span>{' '}
                {createdGift.serviceName}
              </p>
            </div>
            <div
              className="flex items-center gap-3 rounded-2xl px-4 sm:px-5 py-4"
              style={{ background: 'rgba(157,140,255,0.06)', border: '1px solid rgba(157,140,255,0.15)' }}
            >
              <span className="flex-1 font-mono text-base sm:text-xl text-jade tracking-[0.2em] tabular-nums">
                {createdGift.code}
              </span>
              <Button size="md" variant="primary" onClick={copyGiftCode}>Копировать</Button>
            </div>
            <Button variant="ghost" size="lg" className="w-full" onClick={() => setGiftOpen(false)}>Готово</Button>
          </div>
        ) : (
          <div className="px-6 sm:px-7 pb-7 pt-5 space-y-6">
            <div>
              <p className="font-mono text-xs text-text-faint uppercase tracking-wider mb-3">Выберите тариф</p>
              {services && services.length > 0 ? (
                <div className="grid grid-cols-2 gap-2.5">
                  {services.map((svc) => (
                    <button
                      key={svc.id}
                      onClick={() => setGiftServiceId(svc.id)}
                      className="rounded-2xl px-4 py-4 text-left transition-all duration-150 active:scale-[0.98]"
                      style={giftServiceId === svc.id ? {
                        background: 'rgba(157,140,255,0.1)',
                        border: '1px solid rgba(157,140,255,0.28)',
                      } : {
                        background: 'rgba(157,140,255,0.04)',
                        border: '1px solid rgba(157,140,255,0.1)',
                      }}
                    >
                      <p className={`font-display text-lg sm:text-xl leading-tight mb-1 ${giftServiceId === svc.id ? 'text-jade' : 'text-text'}`}>
                        {svc.name}
                      </p>
                      <p className={`font-mono text-sm sm:text-base tabular-nums ${giftServiceId === svc.id ? 'text-jade opacity-75' : 'text-text-dim'}`}>
                        {svc.price.toLocaleString('ru-RU')} ₽
                      </p>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="font-mono text-sm text-text-dim rounded-2xl px-4 py-3"
                  style={{ background: 'rgba(157,140,255,0.04)', border: '1px solid rgba(157,140,255,0.08)' }}>
                  Нет доступных тарифов
                </p>
              )}
            </div>
            <div className="flex gap-3">
              <Button variant="primary" size="lg" className="flex-1" loading={createGift.isPending} disabled={!giftServiceId || !selectedService} onClick={handleCreateGift}>
                Создать подарок
              </Button>
              <Button variant="ghost" size="lg" onClick={() => setGiftOpen(false)}>Отмена</Button>
            </div>
          </div>
        )}
      </Modal>
    </motion.div>
  )
}

export function ReferralsPage() {
  return (
    <div className="px-4 md:px-8 py-8 max-w-3xl mx-auto">
      <ReferralsContent />
    </div>
  )
}

function ReferralIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="text-jade mt-0.5 shrink-0" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M16 11a4 4 0 100-8 4 4 0 000 8zM8 13a3 3 0 100-6 3 3 0 000 6z" />
      <path d="M2.5 20a5.5 5.5 0 0111 0M12 20a5 5 0 0110 0" />
    </svg>
  )
}

function GiftIcon({ large = false }: { large?: boolean }) {
  const size = large ? 32 : 14
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className="text-jade shrink-0" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M20 12v8a2 2 0 01-2 2H6a2 2 0 01-2-2v-8" />
      <path d="M22 7H2v5h20V7zM12 22V7" />
      <path d="M12 7h-2.2a2.8 2.8 0 110-5.6C11.8 1.4 12 3.6 12 7zM12 7h2.2a2.8 2.8 0 100-5.6C12.2 1.4 12 3.6 12 7z" />
    </svg>
  )
}
