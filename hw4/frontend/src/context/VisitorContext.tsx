import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { loadVisitor, saveVisitor, type RivalKey, type Visitor } from '../visitor'

// Part E: the visitor's answer to the welcome question. Setting it re-themes the whole site through
// attributes on <html>: data-era="1920s" (alumni decade themes, eras.css) or data-rival="harvard" (Yale overload).
type State = {
  visitor: Visitor | null
  setVisitor: (v: Visitor | null) => void
  askAgain: number // bumps when the shopper wants to answer the welcome question again
  reset: () => void
  // A rival school named in the chat by someone who didn't answer "Rival". It puts that rival's Dan image
  // on the page (the chat itself shows no rival images) until the conversation moves on. Not saved.
  chatRival: RivalKey | null
  setChatRival: (r: RivalKey | null) => void
  activeRival: RivalKey | 'other' | null // the rival whose banner and Yale overload are showing, if any
}

const Ctx = createContext<State | null>(null)

export function VisitorProvider({ children }: { children: ReactNode }) {
  const [visitor, setState] = useState<Visitor | null>(loadVisitor)
  const [askAgain, setAskAgain] = useState(0)
  const [chatRival, setChatRival] = useState<RivalKey | null>(null)
  const activeRival: RivalKey | 'other' | null =
    visitor?.type === 'rival' && !visitor.rivalModeOff ? (visitor.rival ?? 'other') : chatRival

  const setVisitor = useCallback((v: Visitor | null) => {
    saveVisitor(v)
    setState(v)
  }, [])

  const reset = useCallback(() => {
    saveVisitor(null)
    setState(null)
    setChatRival(null)
    setAskAgain((n) => n + 1)
  }, [])

  useEffect(() => {
    const root = document.documentElement
    // A rival in play outranks the decade theme while it lasts.
    if (visitor?.type === 'alum' && visitor.decade && !activeRival) root.dataset.era = visitor.decade
    else delete root.dataset.era
    if (activeRival) root.dataset.rival = activeRival
    else delete root.dataset.rival
  }, [visitor, activeRival])

  return <Ctx.Provider value={{ visitor, setVisitor, askAgain, reset, chatRival, setChatRival, activeRival }}>{children}</Ctx.Provider>
}

export function useVisitor() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useVisitor must be used inside <VisitorProvider>')
  return ctx
}
