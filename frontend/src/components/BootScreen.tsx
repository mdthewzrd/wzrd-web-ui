import { useState, useEffect } from 'react'
import { useTranslation } from '../i18n'

interface BootScreenProps {
  onComplete: () => void
}

export default function BootScreen({ onComplete }: BootScreenProps) {
  const { t } = useTranslation()
  const [visibleLines, setVisibleLines] = useState(0)
  const [titleVisible, setTitleVisible] = useState(false)
  const [subtitleVisible, setSubtitleVisible] = useState(false)
  const [fadeOut, setFadeOut] = useState(false)
  const [skipped, setSkipped] = useState(false)

  const BOOT_LINES = [
    `☤ wzrd.dev v0.4.0`,
    '',
    `${t('boot.connecting')}`,
    'Reading ~/.hermes/state.db',
    'Scanning memory banks',
    'Indexing skill library',
    'Checking service health',
    'Profiling agent processes',
    '',
    '"I think, therefore I process."',
    '',
    t('boot.ready') + '.',
  ]

  useEffect(() => {
    const titleTimer = setTimeout(() => setTitleVisible(true), 100)
    const subtitleTimer = setTimeout(() => setSubtitleVisible(true), 400)
    const lineTimers = BOOT_LINES.map((_, i) =>
      setTimeout(() => setVisibleLines(i + 1), 700 + i * 100)
    )
    const fadeTimer = setTimeout(() => setFadeOut(true), 700 + BOOT_LINES.length * 100 + 400)
    const completeTimer = setTimeout(onComplete, 700 + BOOT_LINES.length * 100 + 800)

    return () => {
      clearTimeout(titleTimer)
      clearTimeout(subtitleTimer)
      lineTimers.forEach(clearTimeout)
      clearTimeout(fadeTimer)
      clearTimeout(completeTimer)
    }
  }, [onComplete])

  const handleSkip = () => {
    if (!skipped) {
      setSkipped(true)
      onComplete()
    }
  }

  return (
    <div
      className="fixed inset-0 flex flex-col items-center justify-center z-50 transition-opacity duration-500 cursor-pointer select-none"
      style={{
        background: 'var(--hud-bg-deep)',
        opacity: fadeOut ? 0 : 1,
      }}
      onClick={handleSkip}
    >
      {/* Title */}
      <div
        className="gradient-text text-3xl sm:text-5xl font-bold tracking-widest mb-2 transition-all duration-500"
        style={{
          opacity: titleVisible ? 1 : 0,
          transform: titleVisible ? 'translateY(0)' : 'translateY(10px)',
        }}
      >
        wzrd.dev
      </div>

      {/* Subtitle */}
      <div
        className="text-sm sm:text-base tracking-[0.3em] uppercase mb-8 sm:mb-10 transition-all duration-500"
        style={{
          color: 'var(--hud-text-dim)',
          opacity: subtitleVisible ? 1 : 0,
          transform: subtitleVisible ? 'translateY(0)' : 'translateY(6px)',
        }}
      >
        dashboard
      </div>

      {/* Boot text */}
      <div className="text-[13px] w-[90vw] max-w-[400px] px-4">
        {BOOT_LINES.slice(0, visibleLines).map((line, i) => (
          <div key={i} className="py-0.5" style={{
            color: line.startsWith('"') ? 'var(--hud-accent)' :
                   line.startsWith('☤') ? 'var(--hud-primary)' :
                   line.endsWith('.') ? 'var(--hud-success)' :
                   'var(--hud-text-dim)',
            fontStyle: line.startsWith('"') ? 'italic' : 'normal',
          }}>
            {line}
            {i === visibleLines - 1 && (
              <span className="animate-pulse" style={{ color: 'var(--hud-primary)' }}>█</span>
            )}
          </div>
        ))}
      </div>

      <div className="absolute bottom-6 text-[13px]" style={{ color: 'var(--hud-text-dim)' }}>
        tap to skip
      </div>
    </div>
  )
}
