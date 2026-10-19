import { Link } from 'react-router-dom'
import { useVisitor } from '../context/VisitorContext'
import { ERA, RIVALS, decadeDan, rivalDan } from '../visitor'

// Part E: shown under the nav on every page. Alumni see Dan dressed for their decade (and the whole site
// in that decade's style); rivals get the full Yale treatment with Dan's rivalry image.
export default function VisitorBanner() {
  const { visitor, reset } = useVisitor()
  if (visitor?.type === 'alum' && visitor.decade) {
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
  if (visitor?.type === 'rival' && !visitor.rivalModeOff) {
    const r = RIVALS.find((x) => x.key === visitor.rival)
    return (
      <section className="rival-banner" aria-label="You're in Yale country">
        <div className="rival-marquee" aria-hidden>
          <span>YALE · BOOLA BOOLA · YALE · BULLDOGS · YALE · FOR GOD, FOR COUNTRY AND FOR YALE · YALE · BOOLA BOOLA · YALE · BULLDOGS · </span>
          <span>YALE · BOOLA BOOLA · YALE · BULLDOGS · YALE · FOR GOD, FOR COUNTRY AND FOR YALE · YALE · BOOLA BOOLA · YALE · BULLDOGS · </span>
        </div>
        <div className="container rival-banner-inner">
          {r && <img src={rivalDan(r.key)} alt={`Handsome Dan vs. ${r.label}`} />}
          <div>
            <p className="rival-kicker">Visitor from {r ? r.label : 'a rival school'} detected</p>
            <h2>
              You're in <span>YALE</span> country now.
            </h2>
            <p>
              Welcome, {r ? `${r.label} fan` : 'rival'}. Handsome Dan has some thoughts about {r ? r.taunt : 'your school'}. While you're here, may we
              interest you in some proper Yale blue?
            </p>
            <p className="era-actions">
              <Link to="/products?q=yale" className="btn btn-brass">Convert to Yale blue</Link>
              <button className="link-btn" onClick={reset}>Not a rival? Change</button>
            </p>
          </div>
        </div>
      </section>
    )
  }
  return null
}
