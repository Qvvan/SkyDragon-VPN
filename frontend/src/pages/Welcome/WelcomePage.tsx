import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Button } from '../../components/ui/Button'

// ─── Easing curve ─────────────────────────────────────────────────────────────
const ease = [0.16, 1, 0.3, 1] as const

const fadeUp = {
  hidden:  { opacity: 0, y: 24, filter: 'blur(6px)' },
  visible: { opacity: 1, y:  0, filter: 'blur(0px)' },
}

// ─── Feature pills ─────────────────────────────────────────────────────────────
const features = [
  { icon: ShieldIcon,    label: 'Молниеносный VPN'         },
  { icon: GiftIcon,      label: 'Подарочные подписки'       },
  { icon: UsersIcon,     label: '+15 дней за каждого друга' },
  { icon: FlashIcon,     label: '5 дней бесплатно'          },
]

// ─── Steps ────────────────────────────────────────────────────────────────────
const steps = [
  {
    num: '01',
    title: 'Регистрация за 30 секунд',
    desc:  'Только номер телефона. Без почты и карты.',
  },
  {
    num: '02',
    title: 'Активируйте пробный период',
    desc:  '5 дней бесплатно. Без вопросов.',
  },
  {
    num: '03',
    title: 'Подключайтесь везде',
    desc:  'Серверы на 6 континентах.',
  },
]

// ─── Particles ────────────────────────────────────────────────────────────────
const particles = Array.from({ length: 22 }, (_, i) => ({
  id:       i,
  left:     `${(i * 11 + 5) % 100}%`,
  delay:    `${(i * 0.41) % 9}s`,
  duration: `${8 + (i % 6)}s`,
  size:     i % 4 === 0 ? 3 : i % 3 === 0 ? 2 : 1.5,
  drift:    `${(i % 2 === 0 ? 1 : -1) * (8 + (i % 22))}px`,
  opacity:  0.3 + (i % 3) * 0.1,
}))

// ─── Component ────────────────────────────────────────────────────────────────
export function WelcomePage() {
  return (
    <div className="relative min-h-screen bg-bg overflow-hidden">

      {/* ── Aurora background ── */}
      <div className="absolute inset-0 pointer-events-none" aria-hidden>
        {/* Primary violet nebula */}
        <motion.div
          className="aurora-blob absolute"
          style={{
            width: '70vw', height: '50vw',
            top: '-10%', left: '-15%',
            background: 'radial-gradient(ellipse at center, rgba(157,140,255,0.12) 0%, rgba(129,100,255,0.07) 40%, transparent 70%)',
            filter: 'blur(40px)',
          }}
          animate={{ x: [0, 20, 0], y: [0, 15, 0], scale: [1, 1.05, 1] }}
          transition={{ duration: 12, ease: 'easeInOut', repeat: Infinity }}
        />
        {/* Secondary violet nebula */}
        <motion.div
          className="absolute"
          style={{
            width: '50vw', height: '40vw',
            bottom: '5%', right: '-10%',
            background: 'radial-gradient(ellipse at center, rgba(100,80,220,0.09) 0%, transparent 65%)',
            filter: 'blur(50px)',
          }}
          animate={{ x: [0, -18, 0], y: [0, -12, 0] }}
          transition={{ duration: 15, ease: 'easeInOut', repeat: Infinity, delay: 3 }}
        />
        {/* Gold accent nebula */}
        <motion.div
          className="absolute"
          style={{
            width: '30vw', height: '25vw',
            top: '40%', left: '55%',
            background: 'radial-gradient(ellipse at center, rgba(226,185,110,0.05) 0%, transparent 60%)',
            filter: 'blur(35px)',
          }}
          animate={{ x: [0, 12, 0], y: [0, -8, 0] }}
          transition={{ duration: 18, ease: 'easeInOut', repeat: Infinity, delay: 6 }}
        />
      </div>

      {/* ── Particle field ── */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden>
        {particles.map((p) => (
          <span
            key={p.id}
            className="particle absolute rounded-full"
            style={{
              left: p.left,
              bottom: '-6px',
              width:  p.size,
              height: p.size,
              opacity: p.opacity,
              animationDuration: p.duration,
              animationDelay:    p.delay,
              // @ts-expect-error CSS custom property
              '--drift': p.drift,
            }}
          />
        ))}
      </div>

      {/* ── Nav ── */}
      <nav className="relative z-10 flex items-center justify-between px-6 md:px-14 h-16">
        <div className="flex items-center gap-2.5">
          <NavLogoMark />
          <span className="font-display text-[15px] font-medium text-text tracking-[0.16em] uppercase">SkyDragon VPN</span>
        </div>
        <Link
          to="/login"
          className="font-mono text-sm text-text-dim hover:text-jade transition-colors duration-200 flex items-center gap-1.5"
        >
          Войти
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </Link>
      </nav>

      {/* ── Hero ── */}
      <motion.section
        initial="hidden"
        animate="visible"
        variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
        className="relative z-10 flex flex-col items-center text-center px-6 pt-12 pb-24"
      >
        {/* Dragon sigil */}
        <motion.div
          variants={fadeUp}
          transition={{ duration: 0.6, ease }}
          className="mb-12 relative"
        >
          {/* Outer glow halo */}
          <div
            className="absolute inset-0 blur-3xl opacity-50"
            style={{
              background: 'radial-gradient(circle at 50% 50%, rgba(157,140,255,0.4) 0%, rgba(157,140,255,0.1) 50%, transparent 72%)',
            }}
            aria-hidden
          />

          {/* Shield container */}
          <div
            className="relative flex items-center justify-center"
            style={{ width: 164, height: 164 }}
          >
            {/* Slow-spinning outer ring */}
            <motion.div
              className="absolute inset-0 rounded-full"
              style={{
                border: '1px solid rgba(157,140,255,0.2)',
                borderTopColor: 'rgba(157,140,255,0.5)',
                borderRightColor: 'rgba(157,140,255,0.3)',
              }}
              animate={{ rotate: 360 }}
              transition={{ duration: 20, ease: 'linear', repeat: Infinity }}
            />
            {/* Inner ring (counter-rotate) */}
            <motion.div
              className="absolute rounded-full"
              style={{
                inset: 14,
                border: '1px dashed rgba(157,140,255,0.15)',
              }}
              animate={{ rotate: -360 }}
              transition={{ duration: 30, ease: 'linear', repeat: Infinity }}
            />

            {/* Shield */}
            <div
              className="relative flex items-center justify-center rounded-full"
              style={{
                width: 120, height: 120,
                background: 'radial-gradient(circle at 40% 35%, rgba(157,140,255,0.14), rgba(0,0,0,0) 70%)',
                boxShadow: '0 0 0 1px rgba(157,140,255,0.2), 0 0 40px rgba(157,140,255,0.12)',
              }}
            >
              <HeroSigilSVG />
            </div>

            {/* Corner dots */}
            {[0, 90, 180, 270].map((deg) => (
              <motion.div
                key={deg}
                className="absolute w-2 h-2 rounded-full bg-jade"
                style={{
                  top: '50%', left: '50%',
                  marginLeft: -4, marginTop: -4,
                  transformOrigin: '4px 4px',
                  rotate: deg,
                  translateY: -78,
                  boxShadow: '0 0 8px rgba(157,140,255,0.8)',
                }}
                animate={{ opacity: [0.6, 1, 0.6] }}
                transition={{ duration: 2, delay: deg / 360, repeat: Infinity, ease: 'easeInOut' }}
              />
            ))}
          </div>
        </motion.div>

        {/* Eyebrow */}
        <motion.p
          variants={fadeUp}
          transition={{ duration: 0.5, ease }}
          className="font-mono text-[11px] text-jade uppercase tracking-[0.22em] mb-4"
        >
          Приватность нового поколения
        </motion.p>

        {/* Headline */}
        <motion.h1
          variants={fadeUp}
          transition={{ duration: 0.6, ease }}
          className="font-display text-5xl md:text-7xl lg:text-8xl font-light text-text leading-[1.08] max-w-3xl text-balance mb-2"
        >
          Выпусти дракона.
        </motion.h1>
        <motion.h1
          variants={fadeUp}
          transition={{ duration: 0.6, ease }}
          className="font-display text-5xl md:text-7xl lg:text-8xl font-light leading-[1.08] max-w-3xl text-balance mb-6"
          style={{
            background: 'linear-gradient(135deg, #c4b5fd 0%, #9d8cff 50%, #818cf8 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}
        >
          Защити свободу.
        </motion.h1>

        {/* Subtext */}
        <motion.p
          variants={fadeUp}
          transition={{ duration: 0.5, ease }}
          className="font-mono text-sm text-text-dim max-w-sm text-pretty leading-relaxed mb-10"
        >
          Молниеносные серверы на 6 континентах,&nbsp;нулевые логи и&nbsp;безупречное шифрование.
        </motion.p>

        {/* Feature pills */}
        <motion.div
          variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
          className="flex flex-wrap justify-center gap-2.5 mb-10"
        >
          {features.map((f) => (
            <motion.span
              key={f.label}
              variants={fadeUp}
              transition={{ duration: 0.4, ease }}
              className="inline-flex items-center gap-2 rounded-full px-4 py-2"
              style={{
                background: 'rgba(157,140,255,0.06)',
                border: '1px solid rgba(157,140,255,0.14)',
                backdropFilter: 'blur(8px)',
              }}
            >
              <f.icon />
              <span className="font-mono text-[12px] text-text-dim">{f.label}</span>
            </motion.span>
          ))}
        </motion.div>

        {/* CTA */}
        <motion.div
          variants={fadeUp}
          transition={{ duration: 0.4, ease }}
          className="flex flex-col sm:flex-row gap-3"
        >
          <Link to="/register">
            <Button size="lg" variant="primary" className="shadow-[0_0_32px_rgba(157,140,255,0.25)]">
              Начать бесплатно
            </Button>
          </Link>
          <Link to="/login">
            <Button size="lg" variant="ghost">Войти в аккаунт</Button>
          </Link>
        </motion.div>
      </motion.section>

      {/* ── Stats strip ── */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, ease }}
        className="relative z-10 px-6 md:px-14 pb-20"
      >
        <div className="max-w-3xl mx-auto">
          <div className="grid grid-cols-3 divide-x divide-[rgba(157,140,255,0.08)]">
            {[
              { value: '6',     label: 'Континентов'    },
              { value: '99.9%', label: 'Uptime'         },
              { value: '0',     label: 'Логов'           },
            ].map((stat) => (
              <div key={stat.label} className="px-6 text-center first:pl-0 last:pr-0">
                <p
                  className="font-display text-3xl md:text-4xl font-light mb-1"
                  style={{
                    background: 'linear-gradient(135deg, #c4b5fd 0%, #9d8cff 70%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                  }}
                >
                  {stat.value}
                </p>
                <p className="font-mono text-[11px] text-text-faint uppercase tracking-wider">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* ── How it works ── */}
      <section className="relative z-10 px-6 md:px-14 pb-28">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, ease }}
            className="text-center mb-14"
          >
            <p className="font-mono text-[11px] text-jade uppercase tracking-[0.18em] mb-3">Просто. Быстро. Надёжно.</p>
            <h2 className="font-display text-3xl md:text-4xl font-light text-text text-balance">Три шага до защиты</h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {steps.map((step, i) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.12, ease }}
                whileHover={{ y: -4, transition: { type: 'spring', duration: 0.3, bounce: 0 } }}
                className="rounded-[24px] cursor-default"
                style={{
                  background: 'rgba(13,12,31,0.8)',
                  border: '1px solid rgba(157,140,255,0.1)',
                  backdropFilter: 'blur(8px)',
                }}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <span
                      className="font-display text-4xl font-light tabular-nums leading-none"
                      style={{
                        background: 'linear-gradient(135deg, rgba(157,140,255,0.5) 0%, rgba(157,140,255,0.2) 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                      }}
                    >
                      {step.num}
                    </span>
                    <div className="size-8 rounded-full flex items-center justify-center" style={{ background: 'rgba(157,140,255,0.08)' }}>
                      <StepCheckIcon />
                    </div>
                  </div>
                  <h3 className="font-display text-[17px] font-medium text-text mb-2 text-balance">{step.title}</h3>
                  <p className="font-mono text-[13px] text-text-dim leading-relaxed text-pretty">{step.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Final CTA ── */}
      <motion.section
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6, ease }}
        className="relative z-10 px-6 md:px-14 pb-24 text-center"
      >
        <div
          className="max-w-xl mx-auto rounded-[32px] px-8 py-12"
          style={{
            background: 'rgba(13,12,31,0.6)',
            border: '1px solid rgba(157,140,255,0.14)',
            backdropFilter: 'blur(16px)',
          }}
        >
          <p className="font-mono text-[11px] text-jade uppercase tracking-[0.18em] mb-4">Начни сегодня</p>
          <h2 className="font-display text-3xl md:text-4xl font-light text-text text-balance mb-3">
            5 дней бесплатно.
          </h2>
          <p className="font-mono text-sm text-text-dim mb-8 text-pretty">
            Карта не нужна. Только номер телефона.
          </p>
          <Link to="/register">
            <Button size="lg" variant="primary" className="shadow-[0_0_40px_rgba(157,140,255,0.3)]">
              Активировать пробный период
            </Button>
          </Link>
        </div>
      </motion.section>
    </div>
  )
}

// ─── Icons ─────────────────────────────────────────────────────────────────────

function NavLogoMark() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="12" cy="12" r="11" stroke="rgba(157,140,255,0.2)" strokeWidth="1" />
      <path
        d="M12 3.5l7 2.8v6.5c0 4.5-2.5 7.3-7 9.5C7.5 20.1 5 17.3 5 12.8V6.3L12 3.5z"
        fill="rgba(157,140,255,0.08)"
        stroke="rgba(157,140,255,0.7)"
        strokeWidth="1.1"
      />
      <path d="M9 12.2l2 2 4-4" stroke="rgba(157,140,255,0.85)" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function HeroSigilSVG() {
  return (
    <svg width="76" height="76" viewBox="0 0 76 76" fill="none" aria-hidden>
      {/* Outer ring */}
      <circle cx="38" cy="38" r="34" stroke="rgba(157,140,255,0.15)" strokeWidth="1" />
      {/* Inner ring */}
      <circle cx="38" cy="38" r="22" stroke="rgba(157,140,255,0.2)" strokeWidth="1" />
      {/* Cross hairs */}
      <path d="M38 12v10M38 54v10M12 38h10M54 38h10" stroke="rgba(157,140,255,0.3)" strokeWidth="1.4" strokeLinecap="round" />
      {/* Shield body */}
      <path
        d="M38 22l12 4.8v10c0 7-3.8 11.2-12 14.5C26.8 48 23 43.8 23 36.8V26.8L38 22z"
        fill="rgba(157,140,255,0.1)"
        stroke="rgba(157,140,255,0.75)"
        strokeWidth="1.5"
      />
      {/* Checkmark */}
      <path
        d="M30.5 38.5l5.5 5.5 9.5-10.5"
        stroke="rgba(157,140,255,0.95)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Cardinal dots */}
      <circle cx="38" cy="7"  r="1.8" fill="rgba(157,140,255,0.9)" />
      <circle cx="38" cy="69" r="1.8" fill="rgba(157,140,255,0.9)" />
      <circle cx="7"  cy="38" r="1.8" fill="rgba(157,140,255,0.9)" />
      <circle cx="69" cy="38" r="1.8" fill="rgba(157,140,255,0.9)" />
    </svg>
  )
}

function ShieldIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" className="text-jade" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 2l7 3v6c0 5-2.7 8.2-7 10.3C7.7 19.2 5 16 5 11V5l7-3z" />
      <path d="M9.7 11.8l1.6 1.6 3.2-3.2" />
    </svg>
  )
}

function GiftIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" className="text-jade" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M20 12v8a2 2 0 01-2 2H6a2 2 0 01-2-2v-8" />
      <path d="M22 7H2v5h20V7zM12 22V7" />
      <path d="M12 7h-2.2a2.8 2.8 0 110-5.6C11.8 1.4 12 3.6 12 7zM12 7h2.2a2.8 2.8 0 100-5.6C12.2 1.4 12 3.6 12 7z" />
    </svg>
  )
}

function UsersIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" className="text-jade" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M16 11a4 4 0 100-8 4 4 0 000 8M8 13a3 3 0 100-6 3 3 0 000 6" />
      <path d="M2.5 20a5.5 5.5 0 0111 0M12 20a5 5 0 0110 0" />
    </svg>
  )
}

function FlashIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" className="text-jade" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M13 2L5 14h6l-1 8 9-13h-6V2z" />
    </svg>
  )
}

function StepCheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" className="text-jade" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M20 6L9 17l-5-5" />
    </svg>
  )
}
