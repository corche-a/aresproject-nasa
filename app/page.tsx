import Link from "next/link";
import { getData } from "../lib/data";
export default async function Home() {
  const data = await getData();
  const target = data.targets[0];
  const records = data.records.filter((r) => r.basin_id === data.records[0].basin_id);
  const best = records.reduce((a,b) => a.aridity_norm > b.aridity_norm ? a : b);
  return <main className="shell"><section className="hero"><div className="eyebrow">NASA Space Apps Challenge 2026</div><h1>We didn't choose the place.<br/>We asked <span>Mars</span>.</h1><p>NASA data found Earth locations that repeat the closed-basin lake → evaporation → salts → dry bed → wind-lifted dust process.</p><Link className="button" href="/explorer">Open Explorer →</Link></section><section className="grid"><div className="card"><div className="stat">{data.metadata.basins_count}</div><div className="muted">Earth basins</div></div><div className="card"><div className="stat">{data.metadata.total_windows}</div><div className="muted">Basin-month windows</div></div><div className="card"><div className="stat">{best.month_name}</div><div className="muted">Example arid window</div></div><div className="card"><div className="stat">{target.body}</div><div className="muted">First target: {target.name}</div></div></section><section className="grid" style={{marginTop:16}}>{["Closed-basin lake","Evaporite minerals","Wet-to-dry cycle","Active aeolian dust"].map((item)=><article className="card" key={item}><h2>{item}</h2><p className="muted">Source products and proxy measurements are shown per basin. No value is fabricated.</p><div className="label">NASA-derived signal</div></article>)}</section></main>;
}
