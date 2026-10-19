import type { CSSProperties } from 'react'
import type { CustomProduct, Design, Placement } from '../api'

export const DEFAULT_PLACEMENT: Placement = { scale: 0.85, y: 0 }

// Where the (square) design sits on the (square) mockup photo, in fractions of the photo.
export function artRect(product: CustomProduct, placement: Placement) {
  const p = product.print
  if (product.bleed) return { left: p.x, top: p.y, width: p.w, height: p.h }
  const side = Math.min(placement.scale * p.w, p.h)
  const free = p.h - side
  return { left: p.x + (p.w - side) / 2, top: p.y + free * (0.5 + placement.y / 2), width: side, height: side }
}

const pct = (n: number) => `${(n * 100).toFixed(2)}%`

/** Live product preview: blank product photo + the customer's Dan design in the print area.
 *  On light products the photo is multiplied back over the art, so folds and shading show through
 *  like a real print. */
export default function Mockup({
  product,
  design,
  placement = DEFAULT_PLACEMENT,
  className = '',
  showArea = false,
}: {
  product: CustomProduct
  design?: Design | null
  placement?: Placement
  className?: string
  showArea?: boolean
}) {
  const r = artRect(product, placement)
  const art: CSSProperties = { left: pct(r.left), top: pct(r.top), width: pct(r.width), height: pct(r.height) }
  // Shading layer: the same product photo, cropped to the art's box and masked by the art itself, so
  // fabric folds multiply onto the print only (not onto the transparent parts of a sticker).
  const shade: CSSProperties = {
    ...art,
    backgroundImage: `url(${product.mockup_url})`,
    backgroundSize: `${100 / r.width}% ${100 / r.height}%`,
    backgroundPosition: `${pct(r.left / (1 - r.width))} ${pct(r.top / (1 - r.height))}`,
    maskImage: `url(${design?.image_url})`,
    WebkitMaskImage: `url(${design?.image_url})`,
    maskSize: product.bleed ? 'cover' : 'contain',
    WebkitMaskSize: product.bleed ? 'cover' : 'contain',
  }
  const area = product.print
  return (
    <div className={`mockup mockup-${product.key} ${product.dark ? 'dark' : ''} ${className}`}>
      <img className="mockup-base" src={product.mockup_url} alt={`${product.name} (${product.color})`} />
      {showArea && (
        <span
          className="mockup-area"
          style={{ left: pct(area.x), top: pct(area.y), width: pct(area.w), height: pct(area.h) }}
          aria-hidden
        />
      )}
      {design?.image_url && (
        <>
          <img
            key={design.ref}
            className={`mockup-art ${design.style} ${product.bleed ? 'bleed' : ''}`}
            src={design.image_url}
            alt={`Design: ${design.title}`}
            style={art}
          />
          {!product.dark && <span className="mockup-shade" style={shade} aria-hidden />}
        </>
      )}
    </div>
  )
}
