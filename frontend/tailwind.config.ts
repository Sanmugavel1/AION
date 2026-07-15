import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // AION Onyx & Gold Palette — the base was a blue-purple navy fighting
        // the gold accent for attention; shifted to a warm-neutral onyx/
        // charcoal (matching the logo's own near-black) so gold reads as the
        // one deliberate color statement instead of competing with blue.
        // Token NAMES unchanged so every page that reads these tokens flips
        // automatically.
        aion: {
          bg: "#0C0B09",
          surface: "#17140F",
          surface2: "#211C14",
          border: "rgba(255,255,255,0.09)",
          "border-strong": "rgba(255,255,255,0.16)",
          ink: "#F3EFE4",
          "ink-muted": "#A69C8C",
          "ink-faint": "#756B5C",
          sidebar: "#0C0B09",
          "sidebar-hover": "#211C14",
          "sidebar-text": "#A69C8C",
          "sidebar-text-active": "#F3EFE4",
          accent: "#E8B84B",
          "accent-hover": "#F5C860",
          "accent-tint": "rgba(232,184,75,0.14)",
          "accent-border": "rgba(232,184,75,0.32)",
          insight: "#F5D98A",
          "insight-tint": "rgba(245,217,138,0.14)",
          // Secondary hues — used sparingly (1-2 hero moments per page), all tuned
          // to glow correctly against the sapphire base.
          violet: "#A78BFA",
          "violet-tint": "rgba(167,139,250,0.14)",
          "violet-border": "rgba(167,139,250,0.30)",
          teal: "#4FD1C5",
          "teal-tint": "rgba(79,209,197,0.14)",
          "teal-border": "rgba(79,209,197,0.30)",
          rose: "#F472B6",
          "rose-tint": "rgba(244,114,182,0.14)",
          "rose-border": "rgba(244,114,182,0.30)",
        },
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        // Health / status colors — TalentRank's exact signal palette, tuned to
        // glow on dark ink. Semantic meaning (green=healthy/yellow=warning/
        // red=critical) is unchanged from the prior theme, only the hex values
        // and translucent tint/border treatment (rgba, not solid pastel) changed.
        health: {
          green: "#3FCF8E",
          "green-tint": "rgba(63,207,142,0.14)",
          "green-border": "rgba(63,207,142,0.30)",
          yellow: "#F2994A",
          "yellow-tint": "rgba(242,153,74,0.14)",
          "yellow-border": "rgba(242,153,74,0.30)",
          red: "#F45B5B",
          "red-tint": "rgba(244,91,91,0.14)",
          "red-border": "rgba(244,91,91,0.30)",
          critical: "#F45B5B",
          blue: "#6EA8FE",
          purple: "#A78BFA",
          orange: "#F2994A",
        },
      },
      fontFamily: {
        sans: ["var(--font-outfit)", "Outfit", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains)", "JetBrains Mono", "monospace"],
        display: ["var(--font-space-grotesk)", "Space Grotesk", "sans-serif"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "1rem" }],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in-up": {
          from: { opacity: "0", transform: "translateY(20px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in-right": {
          from: { opacity: "0", transform: "translateX(20px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(232,184,75,0)" },
          "50%": { boxShadow: "0 0 0 4px rgba(232,184,75,0.20)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        "spin-slow": {
          from: { transform: "rotate(0deg)" },
          to: { transform: "rotate(360deg)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        "gradient-x": {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        "border-flow": {
          "0%": { backgroundPosition: "0% 50%" },
          "100%": { backgroundPosition: "200% 50%" },
        },
        aurora: {
          "0%, 100%": { transform: "translate(0%, 0%) scale(1)" },
          "25%": { transform: "translate(9%, -12%) scale(1.12)" },
          "50%": { transform: "translate(-6%, 6%) scale(0.94)" },
          "75%": { transform: "translate(-10%, -7%) scale(1.06)" },
        },
        "shimmer-text": {
          to: { backgroundPosition: "200% center" },
        },
        "text-glow-pulse": {
          "0%, 100%": { filter: "drop-shadow(0 0 18px rgba(232,184,75,0.45))" },
          "50%": { filter: "drop-shadow(0 0 32px rgba(232,184,75,0.75))" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.3s ease-out",
        "fade-in-up": "fade-in-up 0.4s ease-out",
        "slide-in-right": "slide-in-right 0.3s ease-out",
        "pulse-glow": "pulse-glow 2.4s ease-in-out infinite",
        shimmer: "shimmer 2s infinite",
        "spin-slow": "spin-slow 10s linear infinite",
        float: "float 6s ease-in-out infinite",
        "gradient-x": "gradient-x 4s ease infinite",
        "border-flow": "border-flow 3s linear infinite",
        aurora: "aurora 9s ease-in-out infinite",
        "shimmer-text": "shimmer-text 5s linear infinite",
        "text-glow-pulse": "text-glow-pulse 3.5s ease-in-out infinite",
      },
      backdropBlur: {
        xs: "2px",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
        "sidebar-gradient": "linear-gradient(180deg, #0C0B09 0%, #100E0A 100%)",
        "accent-glow": "radial-gradient(ellipse at center, rgba(232,184,75,0.20) 0%, transparent 70%)",
        "insight-glow": "radial-gradient(ellipse at center, rgba(245,217,138,0.16) 0%, transparent 70%)",
        "accent-gradient": "linear-gradient(120deg, #E8B84B 0%, #F5D98A 100%)",
        // Premium brand gradient — widened tonal range within the gold family
        // (bronze → gold → pale champagne → gold) for visible movement while
        // staying luxury, not rainbow.
        "brand-gradient": "linear-gradient(120deg, #A9781F 0%, #E8B84B 30%, #FBE7B0 55%, #E8B84B 80%, #C99A34 100%)",
        "brand-mesh": "radial-gradient(ellipse 55% 45% at 15% 15%, rgba(232,184,75,0.24), transparent 60%), radial-gradient(ellipse 50% 45% at 85% 25%, rgba(245,217,138,0.18), transparent 60%), radial-gradient(ellipse 55% 50% at 50% 100%, rgba(79,209,197,0.10), transparent 60%), radial-gradient(ellipse 40% 35% at 50% 45%, rgba(169,120,31,0.18), transparent 65%)",
        "text-gradient-hero": "linear-gradient(160deg, #FFFFFF 0%, #FBF3DE 35%, #F5D98A 65%, #E8B84B 100%)",
        // Shimmer sweep for headline text — the moving highlight technique,
        // not a static clip. Pair with `.shimmer-text` + `animate-shimmer-text`.
        "shimmer-gradient": "linear-gradient(90deg, #F3EFE4 0%, #E8B84B 25%, #F3EFE4 50%, #FBE7B0 75%, #F3EFE4 100%)",
      },
      boxShadow: {
        card: "0 2px 8px rgba(0,0,0,0.45), 0 0 0 1px rgba(255,255,255,0.06)",
        "card-hover": "0 4px 24px rgba(0,0,0,0.5), 0 0 0 1px rgba(232,184,75,0.22)",
        "card-lg": "0 8px 40px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.08)",
        // Colored glow shadows — reserved for hero elements / primary CTAs / featured
        // cards only. Using these on every card is exactly the "childish" mistake
        // to avoid; one or two per page, on the thing that actually deserves emphasis.
        // Deepened this round for more presence (wider spread, higher opacity).
        "glow-accent": "0 0 55px rgba(232,184,75,0.50), 0 0 110px rgba(232,184,75,0.20)",
        "glow-violet": "0 0 32px rgba(167,139,250,0.35)",
        "glow-teal": "0 0 40px rgba(79,209,197,0.42), 0 0 80px rgba(79,209,197,0.16)",
        "glow-rose": "0 0 28px rgba(244,114,182,0.30)",
      },
      zIndex: {
        "60": "60",
        "70": "70",
        "80": "80",
        "90": "90",
        "100": "100",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
