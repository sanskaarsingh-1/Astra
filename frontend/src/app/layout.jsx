import { Space_Grotesk, Inter, JetBrains_Mono, Caveat } from "next/font/google";
import "./globals.css";
import PageTransition from "@/components/PageTransition/PageTransition";
import BottomNavDock from "@/components/BottomNavDock";

const space = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-space",
  display: "swap"
});

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-inter",
  display: "swap"
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-jetbrains",
  display: "swap"
});

const caveat = Caveat({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-caveat",
  display: "swap"
});

export const viewport = {
  themeColor: "#0f1012",
  width: "device-width",
  initialScale: 1
};

export const metadata = {
  title: "Astra AI — Turn Satellite Data into Actionable Insights. | SIH 2026",
  description: "Turn Satellite Data into Actionable Insights. Smart India Hackathon 2026 — Multimodal Remote Sensing Vision-Language Assistant for Astra.",
  keywords: ["SIH 2026", "Astra", "satellite data", "actionable insights", "spatial computing", "computer vision", "react", "nextjs", "satellite imagery", "earth observation"],
  authors: [{ name: "Tushar Mali" }]
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`${space.variable} ${inter.variable} ${jetbrainsMono.variable} ${caveat.variable}`}
    >
      <body className="font-body antialiased bg-black text-foreground">

        {/* SVG clip definition for squircles */}
        <svg width="0" height="0" style={{ position: "absolute" }} aria-hidden="true">
          <defs>
            <clipPath id="squircleClip" clipPathUnits="objectBoundingBox">
              <path d="M 0,0.5 C 0,0 0,0 0.5,0 S 1,0 1,0.5 1,1 0.5,1 0,1 0,0.5"></path>
            </clipPath>
          </defs>
        </svg>

        {children}
        <BottomNavDock />
        <PageTransition />
      </body>
    </html>
  );
}
