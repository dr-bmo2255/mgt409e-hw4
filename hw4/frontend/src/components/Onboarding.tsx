import { useEffect, useMemo, useState } from 'react'
import { DAN_AVATAR, fetchProducts, type ChatProduct, type DanImage, type Product, type Voice } from '../api'
import { useChatResults } from '../context/ChatResultsContext'
import { useVisitor } from '../context/VisitorContext'
import {
  DECADES,
  ERA,
  RIVALS,
  VISITOR_CHOICES,
  WELCOME_QUESTION,
  decadeDan,
  rivalDan,
  type Decade,
  type RivalKey,
  type Visitor,
  type VisitorType,
} from '../visitor'
import Markdown from './Markdown'

type Step = 'ask' | VisitorType | 'done'
type Line = { who: 'bot' | 'me'; text: string; img?: { src: string; alt: string; caption?: string } }

// Part E: the welcome question, asked first thing in the chat. A short scripted conversation (no AI call):
// Student -> which college / school -> that Dan + its products; Alumnus -> which decade -> the whole site in
// that decade's style + decade Dan; Family -> who -> products; Friend -> gift picks; Rival -> which -> Yale overload.
export default function Onboarding({ voice, onDone, onSkip }: { voice: Voice; onDone: () => void; onSkip: () => void }) {
  const { visitor, setVisitor } = useVisitor()
  const chatResults = useChatResults()
  const [step, setStep] = useState<Step>('ask')
  const [lines, setLines] = useState<Line[]>([
    { who: 'bot', text: (voice === 'dan' ? '*perks up both ears* Welcome to Campus Customs! First things first. ' : 'Welcome to Campus Customs! ') + `**${WELCOME_QUESTION}**` },
  ])
  const [products, setProducts] = useState<Product[]>([])

  useEffect(() => {
    fetchProducts().then(setProducts).catch(() => undefined)
  }, [])

  // Dan category images by group (Colleges, Schools, Family), from the catalog.
  const groups = useMemo(() => {
    const m = new Map<string, DanImage[]>()
    for (const p of products) {
      if (!p.dan) continue
      const list = m.get(p.dan.group) ?? []
      if (!list.some((d) => d.asset_id === p.dan!.asset_id)) list.push(p.dan)
      m.set(p.dan.group, list)
    }
    return m
  }, [products])

  const say = (...add: Line[]) => setLines((l) => [...l, ...add])
  const dan = voice === 'dan'

  function showProducts(title: string, list: Product[], dan?: DanImage | null) {
    if (!list.length) return
    chatResults.show({ query: title, title, products: list as unknown as ChatProduct[], voice, seeAllCategory: null, dan: dan ?? null })
  }

  function finish(v: Visitor) {
    setVisitor(v)
    setStep('done')
    onDone()
  }

  function choose(type: VisitorType, label: string) {
    say({ who: 'me', text: label })
    if (type === 'student') {
      say({ who: 'bot', text: dan ? '*wags* A current Bulldog! Which residential college or grad school is yours?' : 'Which residential college or graduate school are you in?' })
    } else if (type === 'alum') {
      say({ who: 'bot', text: dan ? '*stands at attention* Welcome home, old friend! Which decade did you graduate?' : 'Welcome back! Which decade did you graduate? The shop will dress for the occasion.' })
    } else if (type === 'family') {
      say({ who: 'bot', text: dan ? '*tail goes wild* Family! Who are we outfitting today?' : 'Wonderful! Who are we shopping for (or who are you)?' })
    } else if (type === 'rival') {
      say({ who: 'bot', text: dan ? '*narrows eyes* A rival, eh? Which school, if we must ask?' : 'A rival! Which school, if we must ask?' })
    } else {
      // Friend: straight to crowd-pleasing gift picks (the best-stocked style in each category).
      const best = new Map<string, Product>()
      for (const p of products) if ((best.get(p.category)?.total_stock ?? -1) < p.total_stock) best.set(p.category, p)
      const picks = [...best.values()]
      say({
        who: 'bot',
        text: dan
          ? `*fetches a gift box* Shopping for a Bulldog friend? Here are ${picks.length} crowd-pleasers, one from every category. They're on the page now!`
          : `Shopping for a Bulldog friend? Here are ${picks.length} crowd-pleasing gifts, one from every category. They're on the page now.`,
        img: { src: '/media/dan/welcome_dan.webp', alt: 'Handsome Dan', caption: 'Gift picks for a Bulldog friend' },
      })
      showProducts('Gift picks for a Bulldog friend', picks)
      finish({ type: 'friend' })
      return
    }
    setStep(type)
  }

  function pickDan(type: 'student' | 'family', d: DanImage) {
    const label = d.group === 'Colleges' ? `${d.category} College` : d.group === 'Schools' ? `School of ${d.category}` : d.category
    say({ who: 'me', text: label })
    const list = products.filter((p) => p.dan?.asset_id === d.asset_id)
    say({
      who: 'bot',
      text:
        type === 'student'
          ? `${dan ? '*barks proudly* ' : ''}${label} represent! Here's Dan in your colors, and ${list.length} item${list.length === 1 ? '' : 's'} made for you, now on the page.`
          : `${dan ? '*sniffs approvingly* ' : ''}For ${label === 'Mom' || label === 'Dad' ? `a proud Yale ${label}` : `your Yale ${label.toLowerCase()}`}: here's Dan modeling it, and ${list.length} item${list.length === 1 ? '' : 's'} on the page.`,
      img: { src: d.thumb_url, alt: `Handsome Dan: ${d.category}`, caption: d.caption },
    })
    showProducts(type === 'student' ? `${label} gear` : `For ${label}`, list, d)
    finish({ type, dan: d.asset_id, label })
  }

  function pickDecade(decade: Decade) {
    say({ who: 'me', text: `The ${decade}` })
    say({ who: 'bot', text: `${dan ? '*adjusts his period-correct outfit* ' : ''}${ERA[decade].line}`, img: { src: decadeDan(decade, true), alt: `Handsome Dan in the ${decade}`, caption: `Dan, ${decade}` } })
    finish({ type: 'alum', decade })
  }

  function pickRival(key: RivalKey, label: string, taunt: string) {
    say({ who: 'me', text: label })
    say({
      who: 'bot',
      text: `${dan ? '*puffs out his chest* ' : ''}Ah, ${taunt}. Welcome anyway! Just so you know, you're in **Yale country** now. Boola boola!`,
      img: { src: rivalDan(key, true), alt: `Handsome Dan vs. ${label}`, caption: `Dan vs. ${label}` },
    })
    finish({ type: 'rival', rival: key })
  }

  const colleges = groups.get('Colleges') ?? []
  const schools = groups.get('Schools') ?? []
  const family = groups.get('Family') ?? []

  return (
    <div className="onboarding">
      {lines.map((l, i) =>
        l.who === 'me' ? (
          <div key={i} className="bubble bubble-user">{l.text}</div>
        ) : (
          <div key={i} className={`bubble bubble-assistant ${dan ? 'from-dan' : ''}`}>
            {dan && <span className="bubble-who"><img src={DAN_AVATAR} alt="" /> Dan</span>}
            <Markdown text={l.text} />
            {l.img && (
              <figure className="dan-reveal animate">
                <img src={l.img.src} alt={l.img.alt} />
                {l.img.caption && <figcaption>🐶 {l.img.caption}</figcaption>}
              </figure>
            )}
          </div>
        ),
      )}

      {step === 'ask' && !visitor && ( /* answered some other way (e.g. "I'm a rival" typed later): no stale buttons */
        <div className="onboard-choices" role="group" aria-label={WELCOME_QUESTION}>
          {VISITOR_CHOICES.map((c) => (
            <button key={c.type} onClick={() => choose(c.type, c.label)}>{c.label}</button>
          ))}
          <button className="onboard-skip" onClick={onSkip}>Just browsing</button>
        </div>
      )}
      {step === 'student' && (
        <div className="onboard-choices scroll" role="group" aria-label="College or school">
          <span className="onboard-label">Residential colleges</span>
          {colleges.map((d) => <button key={d.asset_id} onClick={() => pickDan('student', d)}>{d.category}</button>)}
          <span className="onboard-label">Graduate &amp; professional schools</span>
          {schools.map((d) => <button key={d.asset_id} onClick={() => pickDan('student', d)}>{d.category}</button>)}
          {!products.length && <span className="onboard-label">Loading…</span>}
        </div>
      )}
      {step === 'family' && (
        <div className="onboard-choices" role="group" aria-label="Family member">
          {family.map((d) => <button key={d.asset_id} onClick={() => pickDan('family', d)}>{d.category}</button>)}
          {!products.length && <span className="onboard-label">Loading…</span>}
        </div>
      )}
      {step === 'alum' && (
        <div className="onboard-choices" role="group" aria-label="Graduation decade">
          {DECADES.map((d) => <button key={d} onClick={() => pickDecade(d)}>{d}</button>)}
        </div>
      )}
      {step === 'rival' && (
        <div className="onboard-choices" role="group" aria-label="Rival school">
          {RIVALS.map((r) => <button key={r.key} onClick={() => pickRival(r.key, r.label, r.taunt)}>{r.label}</button>)}
        </div>
      )}
    </div>
  )
}
