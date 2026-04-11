import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '../../components/ui/Button'
import { Skeleton } from '../../components/ui/Skeleton'
import { useChatMessages, useSendMessage } from '../../hooks/useChat'

export function ChatContent() {
  const { data: messages, isLoading } = useChatMessages()
  const sendMessage = useSendMessage()
  const [text, setText] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || sendMessage.isPending) return
    setText('')
    await sendMessage.mutateAsync(trimmed)
  }

  return (
    <div className="flex flex-col h-full" style={{ minHeight: '60vh' }}>
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {isLoading ? (
          <div className="space-y-3">
            <div className="flex gap-3">
              <Skeleton className="size-8 rounded-full shrink-0" />
              <Skeleton className="h-12 w-48 rounded-2xl" />
            </div>
            <div className="flex gap-3 flex-row-reverse">
              <Skeleton className="h-10 w-36 rounded-2xl" />
            </div>
          </div>
        ) : (
          <>
            <AnimatePresence initial={false}>
              {messages?.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                  className={['flex gap-3 items-end', msg.role === 'user' ? 'flex-row-reverse' : ''].join(' ')}
                >
                  {msg.role === 'support' && (
                    <div className="size-7 rounded-full bg-jade-dim flex items-center justify-center text-jade shrink-0">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                    </div>
                  )}
                  <div className={[
                    'max-w-[72%] rounded-2xl px-4 py-2.5',
                    msg.role === 'user'
                      ? 'bg-jade-dim shadow-[0_0_0_1px_rgba(157,140,255,0.2)]'
                      : 'bg-surface-3 shadow-card',
                  ].join(' ')}>
                    <p className="font-mono text-sm text-text leading-relaxed">{msg.text}</p>
                    <p className="font-mono text-[10px] text-text-dim mt-1 tabular-nums">
                      {new Date(msg.createdAt).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            <AnimatePresence>
              {sendMessage.isPending && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.2 }}
                  className="flex gap-3 items-end"
                >
                  <div className="size-7 rounded-full bg-jade-dim flex items-center justify-center text-jade shrink-0">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <div className="rounded-2xl px-4 py-2.5 bg-surface-3 shadow-card flex items-center gap-1">
                    {[0, 1, 2].map((i) => (
                      <motion.span
                        key={i}
                        className="size-1.5 rounded-full bg-muted"
                        animate={{ opacity: [0.4, 1, 0.4], scale: [0.8, 1, 0.8] }}
                        transition={{ repeat: Infinity, duration: 1.2, delay: i * 0.2, ease: 'easeInOut' }}
                      />
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 pb-4 pt-3 border-t border-[rgba(157,140,255,0.07)] shrink-0">
        <form onSubmit={handleSend} className="flex gap-2">
          <div className="flex-1 flex items-center gap-2 rounded-2xl px-4 h-11 bg-surface-3 shadow-card focus-within:shadow-[0_0_0_1px_rgba(157,140,255,0.38),0_0_0_4px_rgba(157,140,255,0.07)] transition-[box-shadow] duration-200">
            <input
              type="text"
              placeholder="Type a message…"
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="flex-1 bg-transparent outline-none font-mono text-sm text-text placeholder:text-text-faint"
            />
          </div>
          <Button type="submit" variant="primary" size="md" disabled={!text.trim()} loading={sendMessage.isPending}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </Button>
        </form>
      </div>
    </div>
  )
}

export function ChatPage() {
  return <ChatContent />
}
