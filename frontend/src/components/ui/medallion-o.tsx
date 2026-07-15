/**
 * The "O" in AION, styled as the reference logo's rose-gold coin medallion
 * (a quatrefoil/compass engraving) rather than a plain letterform. Sized in
 * `em` units so it scales inline with surrounding text. Pure vector — used
 * for the giant scalable background wordmark, where a raster crop of the
 * reference image kept leaving a faint rectangular tint no matter how the
 * fade was tuned; vector has no background to leave a trace of.
 */
export function MedallionO({ className, style }: { className?: string; style?: React.CSSProperties }) {
  const id = "medallion-o";
  return (
    <svg viewBox="0 0 100 100" className={className} style={style} aria-hidden="true">
      <defs>
        <radialGradient id={`${id}-face`} cx="35%" cy="30%" r="75%">
          <stop offset="0%" stopColor="#E0A688" />
          <stop offset="60%" stopColor="#B76E5A" />
          <stop offset="100%" stopColor="#8A4E3E" />
        </radialGradient>
      </defs>
      <circle cx="50" cy="50" r="48" fill={`url(#${id}-face)`} stroke="#0A0A0C" strokeWidth="3" />
      <circle cx="50" cy="50" r="40" fill="none" stroke="#0A0A0C" strokeWidth="1.2" opacity="0.35" />
      <g fill="none" stroke="#0A0A0C" strokeWidth="2" strokeLinecap="round" opacity="0.55">
        <path d="M50,18 C58,32 58,32 50,50 C42,32 42,32 50,18 Z" />
        <path d="M50,82 C58,68 58,68 50,50 C42,68 42,68 50,82 Z" />
        <path d="M18,50 C32,42 32,42 50,50 C32,58 32,58 18,50 Z" />
        <path d="M82,50 C68,42 68,42 50,50 C68,58 68,58 82,50 Z" />
      </g>
      <circle cx="50" cy="50" r="6" fill="#0A0A0C" opacity="0.6" />
    </svg>
  );
}
