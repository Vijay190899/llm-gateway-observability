import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getHealth, getMetrics } from "./api";
import type { MetricsSummary } from "./types";
import { StatCard } from "./components/StatCard";
import { Donut } from "./components/Donut";
import { CostBars } from "./components/CostBars";
import { Trend } from "./components/Trend";
import { RequestsTable } from "./components/RequestsTable";
import { Playground } from "./components/Playground";
import { compact, ms, usd } from "./lib/format";
import {
  IconActivity,
  IconBolt,
  IconChart,
  IconCoin,
  IconGauge,
  IconLayers,
  IconMoon,
  IconPlay,
  IconShield,
  IconSun,
} from "./components/icons";

type Tab = "overview" | "playground";
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };

export function App() {
  const [tab, setTab] = useState<Tab>("overview");
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [online, setOnline] = useState<boolean | null>(null);
  const [tracing, setTracing] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const m = await getMetrics();
      setMetrics(m);
      setOnline(true);
    } catch {
      setOnline(false);
    }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    refresh();
    getHealth().then((h) => setTracing(h.tracing)).catch(() => {});
    const id = setInterval(refresh, 3000);
    return () => clearInterval(id);
  }, [refresh]);

  const t = metrics?.totals;
  const latencySeries = (metrics?.recent ?? [])
    .filter((r) => !r.blocked)
    .slice(0, 40)
    .map((r) => r.latency_ms)
    .reverse();

  return (
    <div className="app">
      <Sidebar tab={tab} setTab={setTab} />

      <main className="main">
        <Header
          online={online}
          tracing={tracing}
          theme={theme}
          toggleTheme={() => setTheme((v) => (v === "dark" ? "light" : "dark"))}
          tab={tab}
        />

        {tab === "overview" ? (
          <motion.div className="grid" variants={stagger} initial="hidden" animate="show">
            <motion.section className="grid__stats" variants={stagger}>
              <StatCard label="Total requests" value={t?.requests ?? 0} format={(n) => compact(Math.round(n))} icon={<IconActivity />} sublabel={`${compact(Math.round(t?.tokens ?? 0))} tokens routed`} />
              <StatCard label="Cost saved by cache" value={t?.saved_usd ?? 0} format={(n) => usd(n)} accent="var(--cache)" icon={<IconCoin />} sublabel={`${usd(t?.cost_usd ?? 0)} billed upstream`} />
              <StatCard label="Avg latency" value={t?.avg_latency_ms ?? 0} format={(n) => ms(n)} accent="var(--info)" icon={<IconGauge />} sublabel="cache hits return in <5ms" />
              <StatCard label="Blocked by guardrails" value={t?.blocked ?? 0} format={(n) => compact(Math.round(n))} accent="var(--danger)" icon={<IconShield />} sublabel="injection / policy violations" />
            </motion.section>

            <motion.section className="glass card card--donut" variants={fadeUp}>
              <h3 className="card__title"><IconLayers /> Semantic cache</h3>
              <Donut rate={t?.cache_hit_rate ?? 0} hits={t?.cache_hits ?? 0} total={t?.requests ?? 0} />
            </motion.section>

            <motion.section className="glass card card--bars" variants={fadeUp}>
              <h3 className="card__title"><IconCoin /> Spend by model</h3>
              <CostBars rows={metrics?.by_model ?? []} />
            </motion.section>

            <motion.section className="glass card card--trend" variants={fadeUp}>
              <h3 className="card__title"><IconBolt /> Latency, recent requests</h3>
              <Trend points={latencySeries} unit="ms" />
            </motion.section>

            <motion.section className="glass card card--feed" variants={fadeUp}>
              <h3 className="card__title"><IconChart /> Live request feed</h3>
              <RequestsTable rows={metrics?.recent ?? []} />
            </motion.section>
          </motion.div>
        ) : (
          <Playground onSent={refresh} />
        )}
      </main>
    </div>
  );
}

const fadeUp = { hidden: { opacity: 0, y: 18 }, show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } } };

function Sidebar({ tab, setTab }: { tab: Tab; setTab: (t: Tab) => void }) {
  const items: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "overview", label: "Observability", icon: <IconChart /> },
    { id: "playground", label: "Playground", icon: <IconPlay /> },
  ];
  return (
    <aside className="side glass">
      <div className="side__brand">
        <span className="side__logo"><IconLayers /></span>
        <div>
          <div className="side__name">LLM Gateway</div>
          <div className="side__tag">control plane</div>
        </div>
      </div>
      <nav className="side__nav">
        {items.map((it) => (
          <button key={it.id} className={`navitem ${tab === it.id ? "navitem--on" : ""}`} onClick={() => setTab(it.id)}>
            {tab === it.id && <motion.span layoutId="nav-pill" className="navitem__pill" transition={{ type: "spring", stiffness: 400, damping: 32 }} />}
            <span className="navitem__inner">{it.icon}{it.label}</span>
          </button>
        ))}
      </nav>
      <div className="side__foot">
        <div className="side__foot-line">Semantic cache</div>
        <div className="side__foot-line">Guardrails · OWASP LLM Top 10</div>
        <div className="side__foot-line">Rate limiting · cost tracking</div>
      </div>
    </aside>
  );
}

function Header({ online, tracing, theme, toggleTheme, tab }: { online: boolean | null; tracing: boolean; theme: string; toggleTheme: () => void; tab: Tab }) {
  return (
    <header className="head">
      <div>
        <h1 className="head__title">{tab === "overview" ? "Observability" : "Gateway Playground"}</h1>
        <p className="head__sub">
          {tab === "overview"
            ? "One proxy in front of every LLM call — caching, cost, safety and traces in one place."
            : "Send a request the way a team would, and watch the gateway handle it end to end."}
        </p>
      </div>
      <div className="head__right">
        <span className={`status ${online ? "status--ok" : online === false ? "status--down" : ""}`}>
          <span className="status__dot" />
          {online === null ? "connecting" : online ? "gateway live" : "gateway offline"}
        </span>
        {tracing && <span className="status status--trace"><span className="status__dot" />langfuse</span>}
        <button className="iconbtn" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === "dark" ? <IconSun /> : <IconMoon />}
        </button>
      </div>
    </header>
  );
}
