import type { Metadata, Viewport } from "next";
import { Space_Grotesk, Outfit, JetBrains_Mono } from "next/font/google";
import "@/styles/globals.css";
import { Providers } from "./providers";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  title: { default: "AION", template: "%s — AION" },
  description: "An AI Nervous System that continuously senses, understands, predicts, preserves and evolves organizational intelligence.",
  keywords: ["organizational intelligence", "AI", "knowledge management", "enterprise"],
  icons: { icon: "/aion-mark-circle.png" },
};

export const viewport: Viewport = {
  themeColor: "#0C0B09",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${outfit.variable} ${jetbrainsMono.variable}`} suppressHydrationWarning>
      <body className="bg-aion-bg antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
