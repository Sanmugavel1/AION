/**
 * Ambient texture for the dark onyx dashboard canvas — gold-tinted grid +
 * several soft glow "clusters" (blurred orbs at varied positions/sizes,
 * gently drifting) plus a scatter of small static jewel-shard accents
 * (the same visual language as the landing hero's floating shards, kept
 * static here — no canvas animation cost on every dashboard page), so the
 * canvas reads as atmosphere with real depth rather than a plain solid
 * color.
 */
const SHARDS: { top: string; left: string; size: number; rotate: number; color: string }[] = [
  { top: "12%", left: "18%", size: 16, rotate: 15, color: "#E8B84B" },
  { top: "22%", left: "82%", size: 12, rotate: -30, color: "#FBE7B0" },
  { top: "68%", left: "8%", size: 14, rotate: 50, color: "#A9781F" },
  { top: "78%", left: "90%", size: 11, rotate: -12, color: "#E8B84B" },
  { top: "42%", left: "94%", size: 10, rotate: 25, color: "#C97B5F" },
  { top: "6%", left: "48%", size: 9, rotate: 40, color: "#FBE7B0" },
  { top: "88%", left: "34%", size: 12, rotate: -20, color: "#A78BFA" },
  { top: "54%", left: "4%", size: 10, rotate: 8, color: "#E8B84B" },
];

export function DashboardBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden bg-aion-bg">
      {/* Gold-tinted grid texture */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "linear-gradient(rgba(232,184,75,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(232,184,75,0.06) 1px, transparent 1px)",
          backgroundSize: "44px 44px",
          maskImage:
            "radial-gradient(ellipse 85% 65% at 50% 0%, black 0%, transparent 78%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 85% 65% at 50% 0%, black 0%, transparent 78%)",
        }}
      />

      {/* This layer sits behind every dashboard page and never unmounts, so
          it was cut from 7 overlapping blur() layers (up to 45vw wide,
          110px blur, animating forever) to 4 smaller/lighter ones — filter
          blur at that size is one of the most expensive things a browser
          can composite every frame, and 7 of them stacked was stealing GPU
          time from clicks/page-transitions on every single screen.
          motion-reduce: pauses it entirely for prefers-reduced-motion. */}
      <div
        className="animate-aurora motion-reduce:animate-none absolute -left-[10%] -top-[15%] h-[32vw] w-[32vw] rounded-full opacity-[0.16] blur-[70px] will-change-transform"
        style={{ backgroundColor: "#E8B84B" }}
      />
      <div
        className="animate-aurora motion-reduce:animate-none absolute -right-[8%] top-[5%] h-[24vw] w-[24vw] rounded-full opacity-[0.13] blur-[60px] will-change-transform"
        style={{ backgroundColor: "#FBE7B0", animationDelay: "-6s" }}
      />
      <div
        className="animate-aurora motion-reduce:animate-none absolute -left-[6%] bottom-[8%] h-[18vw] w-[18vw] rounded-full opacity-[0.10] blur-[55px] will-change-transform"
        style={{ backgroundColor: "#A78BFA", animationDelay: "-3s" }}
      />
      <div
        className="animate-aurora motion-reduce:animate-none absolute right-[18%] top-[38%] h-[20vw] w-[20vw] rounded-full opacity-[0.09] blur-[60px] will-change-transform"
        style={{ backgroundColor: "#C97B5F", animationDelay: "-9s" }}
      />

      {/* Scattered jewel-shard accents — the same faceted-fragment language
          as the hero, static (no canvas) so every dashboard page gets it for
          near-zero cost. */}
      {SHARDS.map((s, i) => (
        <svg
          key={i}
          className="absolute opacity-[0.16]"
          style={{ top: s.top, left: s.left, width: s.size, height: s.size, transform: `rotate(${s.rotate}deg)` }}
          viewBox="0 0 10 10"
        >
          <polygon points="5,0 10,10 0,10" fill={s.color} />
        </svg>
      ))}
    </div>
  );
}
