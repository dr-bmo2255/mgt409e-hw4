import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import type { ChatProduct, DanImage, Voice } from '../api'

// The latest product matches the chat agent returned. ChatWidget writes them;
// ChatResults renders them on the page as regular product cards.
export type ChatResults = {
  id: number // bumps on every new result set, so the page can scroll to it
  query: string
  title: string
  products: ChatProduct[]
  voice: Voice
  seeAllCategory: string | null
  dan?: DanImage | null
}

type State = {
  results: ChatResults | null
  show: (r: Omit<ChatResults, 'id'>) => void
  clear: () => void
}

const Ctx = createContext<State | null>(null)

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ChatResults | null>(null)
  const show = useCallback((r: Omit<ChatResults, 'id'>) => setResults({ ...r, id: Date.now() }), [])
  const clear = useCallback(() => setResults(null), [])
  return <Ctx.Provider value={{ results, show, clear }}>{children}</Ctx.Provider>
}

export function useChatResults() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return ctx
}
