import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { loadVisitor, saveVisitor, type Visitor } from '../visitor'

// Part E: the visitor's answer to the welcome question. Setting it re-themes the whole site through
// attributes on <html>: data-era="1920s" (alumni decade themes, eras.css) or data-rival="harvard" (Yale overload).
type State = {
  visitor: Visitor | null
  setVisitor: (v: Visitor | null) => void
  askAgain: number // bumps when the shopper wants to answer the welcome question again
  reset: () => void
}

const Ctx = createContext<State | null>(null)

export function VisitorProvider({ children }: { children: ReactNode }) {
  const [visitor, setState] = useState<Visitor | null>(loadVisitor)
  const [askAgain, setAskAgain] = useState(0)

  const setVisitor = useCallback((v: Visitor | null) => {
    saveVisitor(v)
    setState(v)
  }, [])

  const reset = useCallback(() => {
    saveVisitor(null)
    setState(null)
    setAskAgain((n) => n + 1)
  }, [])

  useEffect(() => {
    const root = document.documentElement
    if (visitor?.type === 'alum' && visitor.decade) root.dataset.era = visitor.decade
    else delete root.dataset.era
    if (visitor?.type === 'rival' && !visitor.rivalModeOff) root.dataset.rival = visitor.rival ?? 'other'
    else delete root.dataset.rival
  }, [visitor])

  return <Ctx.Provider value={{ visitor, setVisitor, askAgain, reset }}>{children}</Ctx.Provider>
}

export function useVisitor() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useVisitor must be used inside <VisitorProvider>')
  return ctx
}
