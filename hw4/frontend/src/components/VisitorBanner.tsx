import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useVisitor } from '../context/VisitorContext'
import { ERA, RIVALS, decadeDan, rivalDan } from '../visitor'

// Part E: shown under the nav on every page. Alumni see Dan dressed for their decade (and the whole site
// in that decade's style); rivals get the full Yale treatment with Dan's rivalry image
// (shown only here, 50% larger than the decade image, never in the chat).
export default function VisitorBanner() {
  const { visitor, setVisitor, reset, activeRival, setChatRival } = useVisitor()

  // The banner sits under the nav on every page. When a rival's image goes up, scroll to it so it's seen
  // wherever the shopper is on the site (the chat stays put in its corner).
  // An instant jump, a moment after it renders: inserting the banner shifts the page, and the chat's own smooth
  // scrolling cancels a smooth page scroll.
  useEffect(() => {
    if (!activeRival) return
    const t = setTimeout(() => window.scrollTo({ top: 0 }), 120)
    return () => clearTimeout(t)
  }, [activeRival])

  if (visitor?.type === 'alum' && visitor.decade && !activeRival) {
    const era = ERA[visitor.decade]
    return (
      <section className="era-banner" aria-label={`Campus Customs, ${visitor.decade} edition`}>
        <div className="container era-banner-inner">
          <img src={decadeDan(visitor.decade)} alt={`Handsome Dan dressed for the ${visitor.decade}`} />
          <div>
            <p className="era-kicker">Class of the {visitor.decade} · {era.style} edition</p>
            <h2>Welcome back, Bulldog.</h2>
            <p>{era.line}</p>
            <p className="era-actions">
              <Link to="/products" className="btn btn-brass">Shop the {visitor.decade} look</Link>
              <button className="link-btn" onClick={reset}>Not you? Change</button>
            </p>
          </div>
        </div>
      </section>
    )
  }
  if (activeRival) {
    const r = RIVALS.find((x) => x.key === activeRival)
    const fan = visitor?.type === 'rival' // answered "Rival"; otherwise the school just came up in the chat
    // One click back to the regular site. A rival fan stays a rival (naming the rivalry again brings it back).
    const backToNormal = () => (fan && visitor ? setVisitor({ ...visitor, rivalModeOff: true }) : setChatRival(null))
    return (
      <section className="rival-banner" aria-label="You're in Yale country">
        <button className="rival-close" onClick={backToNormal} aria-label="Back to the regular site" title="Back to the regular site">×</button>
        <div className="rival-marquee" aria-hidden>
          <span>YALE · BOOLA BOOLA · YALE · BULLDOGS · YALE · FOR GOD, FOR COUNTRY AND FOR YALE · YALE · BOOLA BOOLA · YALE · BULLDOGS · </span>
          <span>YALE · BOOLA BOOLA · YALE · BULLDOGS · YALE · FOR GOD, FOR COUNTRY AND FOR YALE · YALE · BOOLA BOOLA · YALE · BULLDOGS · </span>
        </div>
        <div className="container rival-banner-inner">
          {r && <img src={rivalDan(r.key)} alt={`Handsome Dan vs. ${r.label}`} />}
          <div>
            <p className="rival-kicker">{fan ? `Visitor from ${r ? r.label : 'a rival school'} detected` : `Did someone say ${r?.label ?? 'a rival school'}?`}</p>
            <h2>
              You're in <span>YALE</span> country now.
            </h2>
            <p>
              {fan ? `Welcome, ${r ? `${r.label} fan` : 'rival'}. ` : ''}Handsome Dan has some thoughts about {r ? r.taunt : 'your school'}. While you're
              here, may we interest you in some proper Yale blue?
            </p>
            <p className="era-actions">
              <Link to="/products?q=yale" className="btn btn-brass">Convert to Yale blue</Link>
              <button className="btn btn-ghost-light" onClick={backToNormal}>Back to the regular site</button>
              {fan && <button className="link-btn" onClick={reset}>Not a rival? Change</button>}
            </p>
          </div>
        </div>
      </section>
    )
  }
  return null
}
