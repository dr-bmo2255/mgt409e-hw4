import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-grid">
        <div>
          <h3>Campus Customs</h3>
          <p>Bulldog Blue gear for students, alumni, families, and anyone who bleeds Yale blue.</p>
        </div>
        <div>
          <h4>Visit</h4>
          <p>
            57 Broadway
            <br />
            New Haven, CT 06511
          </p>
        </div>
        <div>
          <h4>Shop</h4>
          <ul>
            <li><Link to="/products">All products</Link></li>
            <li><Link to="/products?category=Hoodies">Hoodies</Link></li>
            <li><Link to="/products?category=Crewnecks">Crewnecks</Link></li>
            <li><Link to="/products?category=Quarter-Zips">Quarter-zips</Link></li>
          </ul>
        </div>
        <div>
          <h4>Help</h4>
          <ul>
            <li><Link to="/about">About us</Link></li>
            <li><Link to="/about#returns">Returns &amp; exchanges</Link></li>
            <li><a href="mailto:orderdept@campuscustoms.com">orderdept@campuscustoms.com</a></li>
          </ul>
        </div>
      </div>
      <div className="container footer-bottom">
        <p className="footer-disclaimer">
          <b>Notice:</b> This is not a real retail site. It is not affiliated with Campus Customs. It was created by Dr_BMo for Yale School of Management's class MGT 409E — AI Foundations for Managers.
        </p>
        <span>Class project demo · {new Date().getFullYear()}</span>
      </div>
    </footer>
  )
}
