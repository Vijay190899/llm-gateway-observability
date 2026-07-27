import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { getHealth, getMetrics, seedDemo } from "./api";
import type { MetricsSummary } from "./types";
import { Backdrop } from "./components/Backdrop";
import { Loader } from "./components/Loader";
import { StatCard } from "./components/StatCard";
import { Donut } from "./components/Donut";
import { CostBars } from "./components/CostBars";
import { AreaChart } from "./components/AreaChart";
import { LineChart } from "./components/LineChart";
import { Histogram } from "./components/Histogram";
import { Findings } from "./components/Findings";
import { TimeFilter } from "./components/TimeFilter";
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
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };

export function App() {
  const [tab, setTab] = useState<Tab>("overview");
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [online, setOnline] = useState<boolean | null>(null);
  const [tracing, setTracing] = useState(false);
  const [ready, setReady] = useState(false);
  const [windowSec, setWindowSec] = useState(3600);

  const refresh = useCallback(async (w: number) => {
    try {
      const m = await getMetrics(w);
      setMetrics(m);
      setOnline(true);
    } catch {
      setOnline(false);
    }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  // Hold the intro screen for a beat, then reveal the resolved dashboard.
  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const t = setTimeout(() => setReady(true), reduce ? 300 : 2400);
    return () => clearTimeout(t);
  }, []);

  // First load: seed demo history once if the gateway has no traffic yet.
  useEffect(() => {
    (async () => {
      const m = await getMetrics(86400).catch(() => null);
      if (m && m.totals.requests === 0) {
        await seedDemo(24, 2000);
      }
      getHealth()
        .then((h) => setTracing(h.tracing))
        .catch(() => {});
    })();
  }, []);

  // Poll the selected window; re-fetch immediately when the range changes.
  useEffect(() => {
    refresh(windowSec);
    const id = setInterval(() => refresh(windowSec), 4000);
    return () => clearInterval(id);
  }, [refresh, windowSec]);

  const t = metrics?.totals;
  const series = metrics?.series ?? [];
  const times = series.map((s) => s.t);

  return (
    <>
      <Backdrop />
      <AnimatePresence>{!ready && <Loader key="loader" />}</AnimatePresence>
      <div className="app">
      <Sidebar
        tab={tab}
        setTab={setTab}
        online={online}
        tracing={tracing}
        theme={theme}
        toggleTheme={() => setTheme((v) => (v === "dark" ? "light" : "dark"))}
      />

      <main className="main">
        <Header tab={tab} />

        {tab === "overview" ? (
          <motion.div className="grid" variants={stagger} initial="hidden" animate="show">
            <motion.div className="grid__full" variants={fadeUp}>
              <TimeFilter value={windowSec} onChange={setWindowSec} />
            </motion.div>

            <motion.section className="grid__stats" variants={stagger}>
              <StatCard label="Requests" value={t?.requests ?? 0} format={(n) => compact(Math.round(n))} icon={<IconActivity />} sublabel={`${compact(Math.round(t?.tokens ?? 0))} tokens routed`} />
              <StatCard label="Cost saved by cache" value={t?.saved_usd ?? 0} format={(n) => usd(n)} accent="var(--cache)" icon={<IconCoin />} sublabel={`${usd(t?.cost_usd ?? 0)} billed upstream`} />
              <StatCard label="Avg latency" value={t?.avg_latency_ms ?? 0} format={(n) => ms(n)} accent="var(--info)" icon={<IconGauge />} sublabel={`p95 ${ms(t?.p95_latency_ms ?? 0)}`} />
              <StatCard label="Blocked by guardrails" value={t?.blocked ?? 0} format={(n) => compact(Math.round(n))} accent="var(--danger)" icon={<IconShield />} sublabel="injection / policy violations" />
            </motion.section>

            <motion.section className="glass card card--8" variants={fadeUp}>
              <h3 className="card__title"><IconActivity /> Requests over time</h3>
              <AreaChart
                windowSeconds={windowSec}
                times={times}
                yFormat={(n) => compact(Math.round(n))}
                bands={[
                  { values: series.map((s) => s.misses), color: "var(--chart-a)", label: "upstream" },
                  { values: series.map((s) => s.hits), color: "var(--chart-b)", label: "cache hit" },
                ]}
              />
            </motion.section>

            <motion.section className="glass card card--4" variants={fadeUp}>
              <h3 className="card__title"><IconLayers /> Cache hit rate</h3>
              <Donut rate={t?.cache_hit_rate ?? 0} hits={t?.cache_hits ?? 0} total={t?.requests ?? 0} />
            </motion.section>

            <motion.section className="glass card card--6" variants={fadeUp}>
              <h3 className="card__title"><IconBolt /> Latency over time</h3>
              <LineChart
                windowSeconds={windowSec}
                times={times}
                yFormat={(n) => `${Math.round(n)}ms`}
                lines={[
                  { points: series.map((s) => s.avg_latency_ms), color: "var(--chart-b)", label: "avg" },
                  { points: series.map((s) => s.p95_latency_ms), color: "var(--chart-a)", label: "p95" },
                ]}
              />
            </motion.section>

            <motion.section className="glass card card--6" variants={fadeUp}>
              <h3 className="card__title"><IconCoin /> Spend over time</h3>
              <AreaChart
                windowSeconds={windowSec}
                times={times}
                yFormat={(n) => usd(n)}
                bands={[{ values: series.map((s) => s.cost_usd), color: "var(--chart-b)", label: "cost" }]}
              />
            </motion.section>

            <motion.section className="glass card card--4" variants={fadeUp}>
              <h3 className="card__title"><IconCoin /> Spend by model</h3>
              <CostBars rows={metrics?.by_model ?? []} />
            </motion.section>

            <motion.section className="glass card card--4" variants={fadeUp}>
              <h3 className="card__title"><IconGauge /> Latency distribution</h3>
              <Histogram bins={metrics?.latency_histogram ?? []} color="var(--chart-b)" />
            </motion.section>

            <motion.section className="glass card card--4" variants={fadeUp}>
              <h3 className="card__title"><IconShield /> Guardrail findings</h3>
              <Findings rows={metrics?.findings ?? []} />
            </motion.section>

            <motion.section className="glass card card--full" variants={fadeUp}>
              <h3 className="card__title"><IconChart /> Recent requests</h3>
              <RequestsTable rows={metrics?.recent ?? []} />
            </motion.section>
          </motion.div>
        ) : (
          <Playground onSent={() => refresh(windowSec)} />
        )}
      </main>
      </div>
    </>
  );
}

const fadeUp = { hidden: { opacity: 0, y: 18 }, show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } } };

function Sidebar({
  tab,
  setTab,
  online,
  tracing,
  theme,
  toggleTheme,
}: {
  tab: Tab;
  setTab: (t: Tab) => void;
  online: boolean | null;
  tracing: boolean;
  theme: string;
  toggleTheme: () => void;
}) {
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
        <span className={`status ${online ? "status--ok" : online === false ? "status--down" : ""}`}>
          <span className="status__dot" />
          {online === null ? "connecting" : online ? "gateway live" : "gateway offline"}
        </span>
        {tracing && <span className="status status--trace"><span className="status__dot" />langfuse</span>}
        <button className="iconbtn side__theme" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === "dark" ? <IconSun /> : <IconMoon />}
        </button>
      </div>
    </aside>
  );
}

function Header({ tab }: { tab: Tab }) {
  const overview = tab === "overview";
  return (
    <header className="head">
      <motion.div
        key={tab}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="eyebrow head__eyebrow">{overview ? "OBSERVABILITY" : "PLAYGROUND"}</div>
        <h1 className="head__title serif">LLM Gateway &amp; Observability Platform</h1>
        <p className="head__sub">
          {overview
            ? "A single proxy for every LLM call: semantic caching, guardrails, rate limiting, and cost and latency tracking, in one place."
            : "Send a request the way a team would, and watch the gateway handle it end to end."}
        </p>
      </motion.div>
    </header>
  );
}
