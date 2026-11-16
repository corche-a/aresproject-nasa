import "./globals.css";
import "leaflet/dist/leaflet.css";
import Link from "next/link";
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><header className="nav shell"><Link href="/" className="brand"><img className="brand-logo" src="/logo.png" alt="ARES logo" /><span className="brand-name">ARES</span><span className="brand-divider">/</span><span>ANALOG DISCOVERY</span></Link><nav className="navlinks"><Link href="/">Home</Link><Link href="/explorer">Explorer</Link><Link href="/method">Method</Link><a href="https://github.com/corche-a/aresproject-nasa">GitHub</a></nav></header>{children}<footer className="footer shell">Data credits: NASA POWER, NASA GIBS, EMIT/LP DAAC via AppEEARS, NASADEM and MODIS. ARES is an analogy tool, not a substitute for field validation.</footer></body></html>;
}
