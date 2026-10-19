import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { bagApi, type Bag } from '../api'
import { useAuth } from './AuthContext'

// The shopping bag (Custom Dan Gear) lives in the database per signed-in customer; this keeps
// the nav count and the Bag page in sync after adds, edits and removals.
type BagState = { bag: Bag; setBag: (b: Bag) => void; refresh: () => Promise<void> }

const EMPTY: Bag = { items: [], count: 0, subtotal: 0 }
const BagContext = createContext<BagState | null>(null)

export function BagProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [bag, setBag] = useState<Bag>(EMPTY)

  const refresh = useCallback(async () => {
    if (!user) return setBag(EMPTY)
    setBag(await bagApi.get().catch(() => EMPTY))
  }, [user])

  useEffect(() => {
    void refresh()
  }, [refresh])

  return <BagContext.Provider value={{ bag, setBag, refresh }}>{children}</BagContext.Provider>
}

export function useBag() {
  const ctx = useContext(BagContext)
  if (!ctx) throw new Error('useBag must be used inside <BagProvider>')
  return ctx
}
