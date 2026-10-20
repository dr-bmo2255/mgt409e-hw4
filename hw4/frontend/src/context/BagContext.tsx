import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { bagApi, type Bag } from '../api'
import { useAuth } from './AuthContext'

// The shopping bag has two kinds of lines:
// - Store items (the catalog's "Add to bag"): kept in this browser, so guests can fill a bag without an account.
// - Custom Dan Gear: lives in the database per signed-in customer, because the designs belong to the account.
// The nav badge counts both. Checkout isn't part of the demo, so nothing is ever charged.
export type StoreLine = {
  key: string // product|size|color
  product_id: string
  name: string
  image_url: string
  price: number
  size: string
  color: string | null
  custom_order: boolean // a colorway we don't stock: made to order, ready in 2–3 weeks
  max: number // in-stock quantity for that size (custom orders: 24)
  quantity: number
}

type BagState = {
  bag: Bag // custom gear (server)
  setBag: (b: Bag) => void
  refresh: () => Promise<void>
  store: StoreLine[]
  addStore: (line: Omit<StoreLine, 'key' | 'quantity'>, quantity?: number) => void
  setStoreQty: (key: string, quantity: number) => void
  removeStore: (key: string) => void
  count: number // everything in the bag
  storeSubtotal: number
}

const EMPTY: Bag = { items: [], count: 0, subtotal: 0 }
const STORE_KEY = 'cc_store_bag'
const BagContext = createContext<BagState | null>(null)

function loadStore(): StoreLine[] {
  try {
    const raw = localStorage.getItem(STORE_KEY)
    return raw ? (JSON.parse(raw) as StoreLine[]) : []
  } catch {
    return []
  }
}

export function BagProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [bag, setBag] = useState<Bag>(EMPTY)
  const [store, setStore] = useState<StoreLine[]>(loadStore)

  const refresh = useCallback(async () => {
    if (!user) return setBag(EMPTY)
    setBag(await bagApi.get().catch(() => EMPTY))
  }, [user])

  useEffect(() => {
    void refresh()
  }, [refresh])

  useEffect(() => {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(store))
    } catch {
      /* private mode: the bag lasts for this page only */
    }
  }, [store])

  const addStore = useCallback((line: Omit<StoreLine, 'key' | 'quantity'>, quantity = 1) => {
    const key = `${line.product_id}|${line.size}|${line.color ?? ''}`
    setStore((s) => {
      const existing = s.find((l) => l.key === key)
      if (existing) return s.map((l) => (l.key === key ? { ...l, quantity: Math.min(l.max, l.quantity + quantity) } : l))
      return [...s, { ...line, key, quantity: Math.min(line.max, quantity) }]
    })
  }, [])
  const setStoreQty = useCallback((key: string, quantity: number) => {
    setStore((s) => s.map((l) => (l.key === key ? { ...l, quantity: Math.max(1, Math.min(l.max, quantity)) } : l)))
  }, [])
  const removeStore = useCallback((key: string) => setStore((s) => s.filter((l) => l.key !== key)), [])

  const storeCount = store.reduce((n, l) => n + l.quantity, 0)
  const storeSubtotal = Math.round(store.reduce((n, l) => n + l.price * l.quantity, 0) * 100) / 100

  return (
    <BagContext.Provider
      value={{ bag, setBag, refresh, store, addStore, setStoreQty, removeStore, count: storeCount + bag.count, storeSubtotal }}
    >
      {children}
    </BagContext.Provider>
  )
}

export function useBag() {
  const ctx = useContext(BagContext)
  if (!ctx) throw new Error('useBag must be used inside <BagProvider>')
  return ctx
}
