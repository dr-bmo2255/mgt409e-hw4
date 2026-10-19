import { Link } from 'react-router-dom'

export default function About() {
  return (
    <>
      <section className="hero hero-slim">
        <div className="container hero-inner">
          <p className="eyebrow">About us</p>
          <h1>Outfitting the Bulldog community from Broadway.</h1>
        </div>
      </section>

      <div className="container section prose">
        <h2>Who we are</h2>
        <p>
          Campus Customs is a New Haven shop focused on one thing: comfortable, well-made Yale apparel that people
          actually want to wear. Our storefront sits at 57 Broadway, steps from campus, and our racks
          are stocked with officially licensed gear for students, alumni, parents, and fans.
        </p>

        <h2>What we carry</h2>
        <ul>
          <li><strong>Everyday staples</strong> — tees, crewnecks, hoodies, and quarter-zips in classic Yale navy and heather gray.</li>
          <li><strong>Residential college pride</strong> — crest designs for colleges like Berkeley, Benjamin Franklin, Saybrook, and Timothy Dwight.</li>
          <li><strong>Team and club gear</strong> — left-chest designs for sports from baseball and fencing to sailing and ice hockey.</li>
          <li><strong>Schools and programs</strong> — fleece and quarter-zips for the Schools of Art, Music, Architecture, Divinity, and more.</li>
        </ul>

        <h2>How we help</h2>
        <p>
          Not sure about fit or color? Our online assistant (the chat bubble in the corner) will answer questions
          about prices, sizes, and what's in stock straight from our inventory. If we don't have something, we'll
          tell you plainly rather than guess.
        </p>

        <h2 id="returns">Returns &amp; exchanges</h2>
        <p>
          Changed your mind? Unworn, unwashed items with original tags can be returned within 30 days of shipping.
          Custom and final-sale items can't be returned. Email your tracking number to{' '}
          <a href="mailto:orderdept@campuscustoms.com">orderdept@campuscustoms.com</a> once your return is on its way,
          and refunds typically post within 2–10 business days.
        </p>

        <h2>Come say hi</h2>
        <p>
          Stop by 57 Broadway, New Haven, CT 06511, or{' '}
          <Link to="/products">browse the full collection online</Link>.
        </p>
      </div>
    </>
  )
}
