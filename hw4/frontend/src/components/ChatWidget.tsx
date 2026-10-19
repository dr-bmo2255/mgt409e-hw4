import { Fragment, useEffect, useLayoutEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { DAN_AVATAR, SITE_PAGES, customApi, clearChatHistory, danForProducts, displayName, fetchChatHistory, formatPrice, sendChat, type ChatMessage, type DanImage, type DraftedBrief, type PageContext, type Voice } from '../api'
import { useAuth } from '../context/AuthContext'
import { useChatResults } from '../context/ChatResultsContext'
import { DAN_ERRORS, DAN_GREETINGS, pick } from '../danVoice'
import BriefCard from './BriefCard'
import Onboarding from './Onboarding'
import { useVisitor } from '../context/VisitorContext'
import { RIVALS, aboutRivals, describeVisitor, detectRival, loadVisitor, rivalDan, rivalLabel, saysRival, wantsStartOver, type RivalKey } from '../visitor'
import Markdown from './Markdown'

const VOICES: Record<Voice, { title: string; status: string; greeting: string; placeholder: string; suggestions: string[] }> = {
  brand: {
    title: 'Chat with Campus Customs',
    status: 'Official shop assistant',
    greeting: "Hi! I'm the Campus Customs assistant. Ask me about hoodies, sizes, prices, or what's in stock.",
    placeholder: 'Ask about merch, sizes, or stock…',
    suggestions: ['Navy hoodies under $70', 'Residential college crewnecks', 'What do you have in XXL?'],
  },
  dan: {
    title: 'Chat with Dan',
    status: "Handsome Dan · Yale's bulldog",
    greeting: DAN_GREETINGS[0], // replaced by a random one of DAN_GREETINGS each time a chat starts
    placeholder: 'Ask Dan anything (he may get distracted)…',
    suggestions: ['What should I wear to The Game?', 'Got anything for a Harvard fan?', 'Best gear for hockey season'],
  },
}

// The full set of matches is rendered on the page (ChatResults); the chat shows a few.
const CHAT_THUMBS = 3

function pageContext(pathname: string, search: string): PageContext {
  const params = new URLSearchParams(search)
  const product = pathname.match(/^\/products\/([^/]+)$/)
  return {
    path: pathname,
    product_id: product ? decodeURIComponent(product[1]) : undefined,
    category: params.get('category') ?? undefined,
    search: params.get('q') ?? undefined,
  }
}

function onboardingDismissed(): boolean {
  try {
    return sessionStorage.getItem('cc_onboarding_skipped') === '1'
  } catch {
    return false
  }
}

const BARK_AFTER_MS = 12_000

function barkDismissed(): boolean {
  try {
    return sessionStorage.getItem('cc_bark_dismissed') === '1'
  } catch {
    return false
  }
}

function clearOnboardingSkip() {
  try {
    sessionStorage.removeItem('cc_onboarding_skipped')
  } catch {
    /* storage unavailable */
  }
}

function dismissOnboarding() {
  try {
    sessionStorage.setItem('cc_onboarding_skipped', '1')
  } catch {
    /* storage unavailable */
  }
}

function loadVoice(): Voice {
  try {
    return localStorage.getItem('cc_chat_voice') === 'dan' ? 'dan' : 'brand'
  } catch {
    return 'brand'
  }
}

export default function ChatWidget() {
  const { user } = useAuth()
  const chatResults = useChatResults()
  const location = useLocation()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [voice, setVoice] = useState<Voice>(loadVoice)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // Dan opens with a different line each time a chat starts (Part C2).
  const [danGreeting, setDanGreeting] = useState(() => pick(DAN_GREETINGS))
  // Part E: the welcome question ("Are you a Current Student, Alumnus, Family, Friend or Rival?") is the first
  // thing in the chat for a new visitor. It opens by itself once; "Just browsing" hides it for this visit.
  // Asked only in Dan's voice, as his first question (the Campus Customs side just says hello). The chat no
  // longer opens by itself: after ~12 s unopened, Dan barks from a speech bubble instead.
  const { visitor, setVisitor, askAgain } = useVisitor()
  const [onboarding, setOnboarding] = useState(() => !loadVisitor() && !onboardingDismissed())
  const [onboardKey, setOnboardKey] = useState(0)
  const [onboardDone, setOnboardDone] = useState(false) // answered: keep the transcript visible in either voice
  // Where the welcome question sits: after the messages that existed when it started (saved history, or earlier
  // messages before switching to Dan), so it's visible at the bottom instead of scrolled out of sight at the top.
  const [onboardAfter, setOnboardAfter] = useState(0)
  const [bark, setBark] = useState(false)
  const everOpened = useRef(false)
  const lastError = useRef<string | null>(null)
  // "mini" is the normal corner size; "expanded" grows to at least half the page (still an overlay).
  const [expanded, setExpanded] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const rootRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const v = VOICES[voice]

  // Signed in: restore saved history from the database. Signed out: start fresh.
  useEffect(() => {
    setError(null)
    if (!user) {
      setMessages([])
      return
    }
    fetchChatHistory()
      .then((h) => {
        if (!onboardDone) setOnboardAfter(h.length)
        setMessages(
          h.map((m, i) => ({
            ...m,
            dan: m.role === 'assistant' ? danForProducts(m.products) : null,
            rival: m.role === 'assistant' ? detectRival(h[i - 1]?.content ?? '') : null,
          })),
        )
      })
      .catch(() => setMessages([]))
  }, [user])

  // Attention bark: if nobody has opened the chat ~12 s after arriving, Dan pipes up from a speech bubble.
  useEffect(() => {
    if (open) {
      everOpened.current = true
      setBark(false)
    }
  }, [open])
  useEffect(() => {
    const t = setTimeout(() => {
      if (!everOpened.current && !barkDismissed()) setBark(true)
    }, BARK_AFTER_MS)
    return () => clearTimeout(t)
  }, [])

  // "Not you? Change" (VisitorBanner) asks the welcome question again, in Dan's voice.
  useEffect(() => {
    if (askAgain === 0) return
    void startOver(true)
  }, [askAgain]) // eslint-disable-line

  useEffect(() => {
    try {
      localStorage.setItem('cc_chat_voice', voice)
    } catch {
      /* storage unavailable: voice just won't be remembered */
    }
  }, [voice])

  // Switching to Dan mid-conversation: ask the welcome question below what's already been said.
  useEffect(() => {
    if (voice === 'dan' && onboarding && !onboardDone) setOnboardAfter(messages.length)
  }, [voice]) // eslint-disable-line

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, busy, open, onboardAfter, voice])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open, voice])

  // When new messages make the mini window overflow, grow it so there's less scrolling.
  // Replies carry images (Dan reveal, product thumbnails) that load after the text renders, so the check
  // also runs as those images load, for a few seconds after each new message (found in Problem 11 testing).
  // Only a new message re-arms it, so a manual collapse sticks until the next reply.
  const autoGrow = useRef(false)
  function growIfOverflowing() {
    const el = listRef.current
    if (autoGrow.current && open && !expanded && el && el.scrollHeight > el.clientHeight + 8) {
      autoGrow.current = false
      setExpanded(true)
    }
  }
  useLayoutEffect(() => {
    autoGrow.current = true
    growIfOverflowing()
    const t = setTimeout(() => (autoGrow.current = false), 4000)
    return () => clearTimeout(t)
  }, [messages, open]) // eslint-disable-line

  // Clicking back on the page shrinks an expanded chat to mini size (it stays open).
  useEffect(() => {
    if (!expanded) return
    const onDown = (e: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setExpanded(false)
    }
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setExpanded(false)
    document.addEventListener('pointerdown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [expanded])

  async function send(text: string) {
    const message = text.trim()
    if (!message || busy) return
    // "start over" / "go back to the first question" → the welcome question again (Dan's voice).
    if (wantsStartOver(message)) {
      setInput('')
      return startOver(true)
    }
    // "I'm a rival" without naming a school → Dan asks which one (buttons), no AI call needed.
    if (saysRival(message) && !detectRival(message)) {
      setInput('')
      setVoice('dan')
      setMessages((m) => [
        ...m,
        { role: 'user', content: message },
        { role: 'assistant', voice: 'dan', ask: 'rival', content: '*narrows his eyes and sniffs suspiciously* A rival, eh? **Which school, if we must ask?**' },
      ])
      return
    }
    // Rival mode (Yale overload) lasts while the chat is about rivals. When the shopper moves on, the site goes
    // back to its normal look; naming a rival again (or the rivalry) switches it back on.
    if (visitor?.type === 'rival') {
      const named = detectRival(message)
      if (!aboutRivals(message)) {
        if (!visitor.rivalModeOff) setVisitor({ ...visitor, rivalModeOff: true })
      } else if (visitor.rivalModeOff || (named && named !== visitor.rival)) {
        setVisitor({ ...visitor, rival: named ?? visitor.rival, rivalModeOff: false })
      }
    }
    const previous = [...messages].reverse().find((m) => m.role === 'assistant')
    const history = messages.map(({ role, content }) => ({ role, content }))
    setMessages((m) => [...m, { role: 'user', content: message }])
    setInput('')
    setError(null)
    setBusy(true)
    try {
      const page = pageContext(location.pathname, location.search)
      const res = await sendChat({ message, voice, previous_voice: previous?.voice ?? null, history, page, visitor: describeVisitor(visitor) })
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          content: res.reply,
          products: res.products,
          voice: res.voice,
          dan: res.dan ?? danForProducts(res.products),
          design: res.design,
          rival: detectRival(message), // another Ivy named → that rival's Dan image appears with the reply
          go_to: res.go_to,
        },
      ])
      // "Take me to Design with Dan": go there now (the chat stays open, shrunk so the page is visible).
      if (res.go_to && SITE_PAGES[res.go_to] && location.pathname !== SITE_PAGES[res.go_to].path) {
        setExpanded(false)
        navigate(SITE_PAGES[res.go_to].path)
      }
      // API contract: the agent's structured matches go onto the page as product cards.
      if (res.products.length > 0) {
        chatResults.show({
          query: message,
          title: res.results_title ?? 'Matches',
          products: res.products,
          voice: res.voice,
          seeAllCategory: res.see_all_category,
          dan: res.dan ?? danForProducts(res.products),
        })
      }
    } catch (err) {
      // Offline or any other failure: Dan explains it in his own voice (one of 5 lines), never a generic error.
      // One exception: a fresh install without a Portkey key, where Dan also says exactly how to fix it.
      if (err instanceof Error && err.message.includes('PORTKEY_API_KEY')) {
        setError("*sits politely, waiting for a treat* I can't chat until I get my Portkey key. Add `PORTKEY_API_KEY` to `hw4/.env` and restart the backend.")
      } else {
        lastError.current = pick(DAN_ERRORS, lastError.current ?? undefined) // never the same line twice in a row
        setError(lastError.current)
      }
      setMessages((m) => m.slice(0, -1)) // un-send so they can retry
      setInput(message)
    } finally {
      setBusy(false)
    }
  }

  // New chat, "start over", and "Not you? Change" all go back to the welcome question. It shows in Dan's
  // voice; toDan switches to Dan so the question appears right away.
  async function startOver(toDan: boolean) {
    if (user) await clearChatHistory().catch(() => undefined)
    setMessages([])
    setError(null)
    setExpanded(false)
    setDanGreeting((g) => pick(DAN_GREETINGS, g))
    setVisitor(null) // the answer (and its theme) is re-chosen
    clearOnboardingSkip()
    setOnboarding(true)
    setOnboardDone(false)
    setOnboardAfter(0)
    setOnboardKey((k) => k + 1)
    chatResults.clear()
    if (toDan) setVoice('dan')
    setOpen(true)
  }

  function newChat() {
    return startOver(false)
  }

  // Rival picked from Dan's "which school?" buttons in the middle of a conversation.
  function pickRival(key: RivalKey) {
    const r = RIVALS.find((x) => x.key === key)!
    setMessages((m) => [
      ...m.map((x) => ({ ...x, ask: undefined })),
      { role: 'user', content: r.label },
      { role: 'assistant', voice: 'dan', rival: key, content: `*puffs out his chest* Ah, ${r.taunt}. Welcome anyway! Just so you know, you're in **Yale country** now. Boola boola!` },
    ])
    setVisitor({ type: 'rival', rival: key })
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    void send(input)
  }

  // Part E welcome question (Dan's voice). Choosing an alumni decade restyles the whole site, so the chat steps aside:
  // after a moment to read Dan's line, it closes to the corner and the page scrolls to the top.
  const onboardingEl =
    onboarding && (voice === 'dan' || onboardDone) ? (
      <Onboarding
        key={onboardKey}
        voice="dan"
        onDone={(chosen) => {
          setOnboardDone(true)
          if (chosen.type === 'alum') {
            setTimeout(() => {
              setExpanded(false)
              setOpen(false)
              window.scrollTo({ top: 0, behavior: 'smooth' })
            }, 1800)
          }
        }}
        onSkip={() => {
          dismissOnboarding()
          setOnboarding(false)
        }}
      />
    ) : null

  return (
    <div ref={rootRef} className={`chat ${open ? 'chat-open' : ''} voice-${voice}`}>
      {open && (
        <section className={`chat-panel ${expanded ? 'expanded' : ''}`} role="dialog" aria-label={v.title}>
          <header className="chat-head">
            <div className="chat-avatar" aria-hidden>{voice === 'dan' ? <img src={DAN_AVATAR} alt="" /> : 'CC'}</div>
            <div className="chat-title">
              <strong>{v.title}</strong>
              <span className="chat-status">{v.status}</span>
            </div>
            {(messages.length > 0 || visitor || onboardDone) && (
              <button className="chat-new" onClick={() => void newChat()} title="Start over: back to Dan's first question">
                New chat
              </button>
            )}
            <button
              className="chat-size"
              onClick={() => setExpanded((x) => !x)}
              aria-label={expanded ? 'Collapse chat to mini size' : 'Expand chat'}
              title={expanded ? 'Collapse to mini size' : 'Expand'}
            >
              {expanded ? '⤡' : '⤢'}
            </button>
            <button className="chat-close" onClick={() => { setOpen(false); setExpanded(false) }} aria-label="Close chat">
              ×
            </button>
          </header>

          <div className="voice-toggle" role="radiogroup" aria-label="Chat voice">
            {(['brand', 'dan'] as Voice[]).map((key) => (
              <button
                key={key}
                role="radio"
                aria-checked={voice === key}
                className={voice === key ? 'active' : ''}
                onClick={() => setVoice(key)}
                disabled={busy}
              >
                {VOICES[key].title}
              </button>
            ))}
          </div>

          <div className="chat-list" ref={listRef} aria-live="polite" onLoadCapture={growIfOverflowing}>
            {onboardingEl && onboardAfter === 0 ? (
              onboardingEl
            ) : (
              <div className="bubble bubble-assistant">
                <Markdown text={voice === 'dan' ? danGreeting : v.greeting} />
              </div>
            )}
            {messages.map((m, i) => (
              <Fragment key={i}>
              <div className={`bubble bubble-${m.role} ${m.voice === 'dan' ? 'from-dan' : ''}`}>
                {m.role === 'assistant' && m.voice && <span className="bubble-who">{m.voice === 'dan' ? 'Dan' : 'Campus Customs'}</span>}
                <Markdown text={m.content} />
                {m.design && <ChatDesign brief={m.design} onOpen={() => setExpanded(false)} />}
                {m.go_to && SITE_PAGES[m.go_to] && (
                  <Link to={SITE_PAGES[m.go_to].path} className="chat-goto" onClick={() => setExpanded(false)}>
                    Go to {SITE_PAGES[m.go_to].label} →
                  </Link>
                )}
                {m.rival && (
                  <figure className={`dan-reveal ${i === messages.length - 1 ? 'animate' : ''}`}>
                    <img src={rivalDan(m.rival as RivalKey, true)} alt={`Handsome Dan vs. ${rivalLabel(m.rival as RivalKey)}`} />
                    <figcaption>🐶 Dan vs. {rivalLabel(m.rival as RivalKey)}</figcaption>
                  </figure>
                )}
                {m.ask === 'rival' && i === messages.length - 1 && (
                  <div className="onboard-choices" role="group" aria-label="Rival school">
                    {RIVALS.map((r) => <button key={r.key} onClick={() => pickRival(r.key)}>{r.label}</button>)}
                  </div>
                )}
                {!m.rival && m.dan && m.products && m.products.length > 0 && <DanReveal dan={m.dan} animate={i === messages.length - 1} />}
                {m.products && m.products.length > 0 && (
                  <div className={`chat-products ${m.dan && i === messages.length - 1 ? 'after-reveal' : ''}`}>
                    {m.products.slice(0, CHAT_THUMBS).map((p) => {
                      const inStock = p.inventory.filter((s) => s.quantity > 0).map((s) => s.size)
                      return (
                        <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-product">
                          <img src={p.image_url} alt="" />
                          <span>
                            {displayName(p.name)}
                            <small>
                              {formatPrice(p.price)} · {inStock.length ? `In stock: ${inStock.join(', ')}` : 'Sold out'}
                            </small>
                          </span>
                        </Link>
                      )
                    })}
                    {m.products.length > CHAT_THUMBS && (
                      <span className="chat-more">+{m.products.length - CHAT_THUMBS} more shown on the page</span>
                    )}
                  </div>
                )}
              </div>
              {onboardingEl && onboardAfter > 0 && i === onboardAfter - 1 ? onboardingEl : null}
              </Fragment>
            ))}
            {busy && (
              <div className="bubble bubble-assistant typing" aria-label="Assistant is typing">
                <span className="paws" aria-hidden>
                  <i>🐾</i>
                  <i>🐾</i>
                  <i>🐾</i>
                </span>
                <span className="sr-only">{voice === 'dan' ? 'Dan is sniffing around…' : 'Typing…'}</span>
              </div>
            )}
            {messages.length === 0 && !busy && !onboarding && (
              <div className="chat-suggestions">
                {v.suggestions.map((s) => (
                  <button key={s} onClick={() => void send(s)}>
                    {s}
                  </button>
                ))}
              </div>
            )}
            {error && (
              <div className="bubble bubble-assistant from-dan chat-error-dan" role="alert">
                <span className="bubble-who"><img src={DAN_AVATAR} alt="" /> Dan</span>
                <Markdown text={error} />
              </div>
            )}
          </div>

          {!user && (
            <p className="chat-guest">
              <Link to="/login" onClick={() => setOpen(false)}>Log in</Link> to save this chat.
            </p>
          )}
          <form className="chat-form" onSubmit={onSubmit}>
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={v.placeholder}
              aria-label="Chat message"
              maxLength={2000}
            />
            <button type="submit" disabled={!input.trim() || busy}>
              Send
            </button>
          </form>
        </section>
      )}

      {bark && !open && (
        <BarkBubble
          onOpen={() => {
            setVoice('dan')
            setOpen(true)
          }}
          onDismiss={() => {
            try {
              sessionStorage.setItem('cc_bark_dismissed', '1')
            } catch {
              /* storage unavailable */
            }
            setBark(false)
          }}
        />
      )}
      <button
        className="chat-fab"
        onClick={() => {
          if (!open && messages.length === 0) setDanGreeting((g) => pick(DAN_GREETINGS, g))
          setOpen((o) => !o)
          setExpanded(false)
        }}
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        {open ? '×' : <img className="chat-fab-face" src={DAN_AVATAR} alt="" />}
        {!open && <span className="chat-fab-label">{voice === 'dan' ? 'Chat with Dan' : 'Chat with us'}</span>}
      </button>
    </div>
  )
}

// The Handsome Dan image for the search's category pops in BEFORE the products (Problem 10, Part B).
function DanReveal({ dan, animate }: { dan: DanImage; animate: boolean }) {
  return (
    <figure className={`dan-reveal ${animate ? 'animate' : ''}`}>
      <img src={dan.thumb_url} alt={`Handsome Dan: ${dan.category}`} />
      <figcaption>🐶 {dan.caption}</figcaption>
    </figure>
  )
}

// A custom Dan design the agent drafted (Problem 10 Part C). Creating it goes through the same
// server guards as the Design with Dan page, then the page shows Dan "posing" until it's ready.
function ChatDesign({ brief, onOpen }: { brief: DraftedBrief; onOpen: () => void }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [created, setCreated] = useState<string | null>(null) // design ref, once this brief has been created

  async function create() {
    if (!user) return navigate('/login')
    setBusy(true)
    setError(null)
    try {
      const d = await customApi.create(brief.brief_id)
      setCreated(d.ref)
      onOpen()
      navigate(`/custom?design=${encodeURIComponent(d.ref)}`)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="chat-design">
      <BriefCard
        brief={brief}
        busy={busy}
        onCreate={created ? undefined : () => void create()}
        action={user ? 'Create this Dan' : 'Log in to create this Dan'}
        note={
          created ? (
            <Link to={`/custom?design=${encodeURIComponent(created)}`} onClick={onOpen}>Dan is on it. View it on Design with Dan →</Link>
          ) : (
            error ?? (user ? 'Uses 1 of your daily creations (3 a day). Saved in your account for 90 days. Then pick the gear on Design with Dan.' : 'Free with an account: 3 creations a day.')
          )
        }
      />
    </div>
  )
}

// Part E follow-up: Dan "barks" from a speech bubble to get attention when nobody has opened the chat yet.
const BARKS = ['Woof!', 'Woof! Woof!', '*sniff sniff* Psst… over here!', "I'm Handsome Dan! Want help finding gear?"]

function BarkBubble({ onOpen, onDismiss }: { onOpen: () => void; onDismiss: () => void }) {
  const [i, setI] = useState(0)
  useEffect(() => {
    // Bark through the lines, rest on the invitation, then bark again every few seconds.
    const t = setTimeout(() => setI((n) => (n + 1) % (BARKS.length + 3)), i < BARKS.length - 1 ? 1300 : 2600)
    return () => clearTimeout(t)
  }, [i])
  const line = BARKS[Math.min(i, BARKS.length - 1)]
  return (
    <div className="bark-bubble" role="status">
      <button className="bark-text" onClick={onOpen} aria-label="Open chat with Handsome Dan">
        <span key={line} className={i < 2 ? 'barking' : 'settle'}>
          <Markdown text={line} />
        </span>
      </button>
      <button className="bark-close" onClick={onDismiss} aria-label="Dismiss">×</button>
    </div>
  )
}
