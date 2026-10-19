import { useCallback, useEffect, useState } from 'react'
import { get, money } from './api'
import Overview, { type OverviewData } from './views/Overview'
import Mapping from './views/Mapping'
import Queue from './views/Queue'
import Review from './views/Review'
import Batch from './views/Batch'
import Settings from './views/Settings'
import Export from './views/Export'
import Chat from './views/Chat'

const TABS = [
  ['overview', 'Overview'],
  ['mapping', 'Catalogue mapping'],
  ['queue', 'Asset queue'],
  ['review', 'Generate / Review'],
  ['chat', '🐶 Ask Dan chat'],
  ['batch', 'Batch control'],
  ['settings', 'Settings'],
  ['export', 'Export'],
] as const
type Tab = (typeof TABS)[number][0]

function readHash(): { tab: Tab; asset?: string } {
  const [tab, asset] = window.location.hash.replace('#', '').split('/')
  return { tab: (TABS.some(([t]) => t === tab) ? tab : 'overview') as Tab, asset }
}

export default function App() {
  const [{ tab, asset }, setRoute] = useState(readHash)
  const [ov, setOv] = useState<OverviewData | null>(null)
  const [err, setErr] = useState<string | null>(null)

  const refresh = useCallback(() => {
    get<OverviewData>('/api/overview')
      .then((d) => {
        setOv(d)
        setErr(null)
      })
      .catch((e) => setErr(String(e)))
  }, [])

  useEffect(() => {
    refresh()
    const t = setInterval(refresh, 2500)
    const onHash = () => setRoute(readHash())
    window.addEventListener('hashchange', onHash)
    return () => {
      clearInterval(t)
      window.removeEventListener('hashchange', onHash)
    }
  }, [refresh])

  const go = (t: Tab, a?: string) => {
    window.location.hash = a ? `${t}/${a}` : t
  }

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <span className="logo">🐶</span>
          <div>
            <strong>Ask Dan Image Studio</strong>
            <small>Campus Customs · catalogue Dan assets · human-approved</small>
          </div>
        </div>
        {ov && (
          <div className="top-stats">
            <span className={`pill ${ov.provider === 'openai' ? 'pill-paid' : 'pill-mock'}`}>
              {ov.provider === 'openai' ? 'PAID provider' : 'MOCK provider ($0)'}
            </span>
            <span className="pill">
              Spent {money(ov.spent_usd)} / cap {money(ov.cost_cap_usd)}
            </span>
            <span className="pill">
              {ov.scoped_approved}/{ov.scoped_total} approved
            </span>
            {ov.current_job?.asset_id && <span className="pill pill-busy">⏳ {ov.current_job.asset_id}</span>}
            {ov.paused && <span className="pill pill-warn">⏸ paused</span>}
          </div>
        )}
      </header>
      <nav className="tabs">
        {TABS.map(([t, label]) => (
          <button key={t} className={t === tab ? 'active' : ''} onClick={() => go(t)}>
            {label}
          </button>
        ))}
      </nav>
      {err && <div className="banner error">Backend unreachable: {err}</div>}
      <main className="content">
        {tab === 'overview' && <Overview data={ov} go={go} />}
        {tab === 'mapping' && <Mapping go={go} />}
        {tab === 'queue' && <Queue go={go} />}
        {tab === 'review' && <Review assetId={asset} go={go} overview={ov} refresh={refresh} />}
        {tab === 'chat' && <Chat overview={ov} refresh={refresh} go={go} />}
        {tab === 'batch' && <Batch overview={ov} refresh={refresh} go={go} />}
        {tab === 'settings' && <Settings refresh={refresh} />}
        {tab === 'export' && <Export />}
      </main>
    </div>
  )
}
