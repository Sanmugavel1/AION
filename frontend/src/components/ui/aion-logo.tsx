/**
 * AION's mark — the real brand emblem (`public/aion-mark-circle.png`,
 * cropped from the user's own Gemini-generated logo artwork), not a
 * hand-drawn approximation. Used at every size (nav/sidebar/footer/auth)
 * so there is one actual brand mark, not several different attempts at
 * redrawing it.
 */
export function AionLogo({ size = 32, className }: { size?: number; className?: string }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/aion-mark-circle.png"
      alt="AION"
      width={size}
      height={size}
      style={{ width: size, height: size }}
      className={className}
      draggable={false}
    />
  );
}
