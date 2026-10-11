import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  AlertCircle,
  BookOpenText,
  CalendarDays,
  CheckCircle2,
  Clock3,
  GitCompare,
  LayoutDashboard,
  Map,
  Menu,
  Pause,
  Play,
  Radio,
  RefreshCw,
  RotateCcw,
  Route,
  ShieldCheck,
  Siren,
  Truck,
  X,
  XCircle,
} from "lucide-react";
import { useInitialPlan } from "./api/hooks";
import { api, Diff, Plan, Proposal, Route as PlanRoute, Scenario, Stop } from "./api/client";
import { minutes } from "./lib/format";
import { scaleTime } from "./lib/timeScale";
import { sessionStore, useSessionStore } from "./store/sessionStore";
import { vehicleRouteColor } from "./lib/routeColors";
import "./styles/globals.css";
import { ScheduleMap } from "./features/map/ScheduleMap";
import { toMapRoutes } from "./features/map/adaptPlan";
import type { CityMap } from "./features/map/cityGraph";

function Kpi({ label, value, note, icon }: { label: string; value: string; note: string; icon: ReactNode }) {
  return <article className="p12-kpi"><div className="p12-kpi-label">{icon}{label}</div><strong>{value}</strong><span>{note}</span></article>;
}

function Gantt({ plan, scenario, clock }: { plan: Plan; scenario: Scenario; clock: number }) {
  const { hoveredDelivery } = useSessionStore();
  const stops = plan.routes.flatMap((route) => route.stops);
  const end = Math.max(scenario.start_time + 60, ...stops.map((stop) => stop.depart + 20));
  const start = scenario.start_time;
  const axis = Array.from({ length: Math.ceil((end - start) / 30) + 1 }, (_, index) => start + index * 30);
  return <div className="p12-gantt">
    <div className="p12-axis"><span>VEHICLE / TIME</span><div>{axis.map((tick) => <span key={tick} style={{ left: `${scaleTime(tick, start, end)}%` }}>{minutes(tick)}</span>)}</div></div>
    {plan.routes.map((route) => <div className="p12-route-row" key={route.vehicle_id}>
      <div className="p12-route-label"><b>{route.vehicle_id}</b><span>{scenario.vehicles.find((vehicle) => vehicle.id === route.vehicle_id)?.name ?? "Vehicle"}</span></div>
      <div className="p12-track">
        {route.stops.map((stop, stopIndex) => <StopBlock key={`${route.vehicle_id}-${stopIndex}`} stop={stop} routeColor={vehicleRouteColor(route.vehicle_id, scenario.vehicles.map((item) => item.id))} start={start} end={end} highlighted={hoveredDelivery === stop.delivery_id} />)}
        <div className="p12-now" style={{ left: `${scaleTime(clock, start, end)}%` }} />
      </div>
    </div>)}
    <div className="p12-axis-footer"><span /><span>Hatched segments indicate waiting before a delivery window.</span></div>
  </div>;
}

function SimulationClock({ clock, start, end, playing, onClock, onPlaying, onReset }: { clock: number; start: number; end: number; playing: boolean; onClock: (value: number) => void; onPlaying: (value: boolean) => void; onReset: () => void }) {
  return <section className="p12-clock-bar" aria-label="Simulation clock">
    <button className="p12-small-button" onClick={() => onPlaying(!playing)}>{playing ? <Pause size={14} /> : <Play size={14} />} {playing ? "Pause" : "Play"}</button>
    <button className="p12-small-button" onClick={onReset}><RotateCcw size={14} /> Reset</button>
    <span className="p12-clock-label">SIMULATION CLOCK <b>{minutes(clock)}</b></span>
    <input aria-label="Simulation time" type="range" min={start} max={end} value={clock} onChange={(event) => { onPlaying(false); onClock(Number(event.target.value)); }} />
    <span className="p12-simulation-note">NOT LIVE GPS</span>
  </section>;
}

function StopBlock({ stop, routeColor, start, end, highlighted }: { stop: Stop; routeColor: string; start: number; end: number; highlighted: boolean }) {
  const left = scaleTime(stop.arrival, start, end);
  const width = Math.max(2, scaleTime(stop.depart, start, end) - left);
  return <div className={`p12-stop-block ${stop.wait ? "is-wait" : ""} ${highlighted ? "is-highlighted" : ""}`} style={{ left: `${left}%`, width: `${width}%`, borderColor: routeColor }} onMouseEnter={() => sessionStore.setHovered(stop.delivery_id ?? null)} onMouseLeave={() => sessionStore.setHovered(null)} title={`${stop.delivery_id ?? "Depot"} · arrival ${minutes(stop.arrival)} · wait ${stop.wait}m · depart ${minutes(stop.depart)}`}>
    <span>{stop.delivery_id ?? "DEPOT"}</span>
  </div>;
}

function LoadProfile({ plan, scenario }: { plan: Plan; scenario: Scenario }) {
  const end = Math.max(scenario.start_time + 60, ...plan.routes.flatMap((route) => route.stops.map((stop) => stop.depart + 20)));
  return <div className="p12-loads"><div className="p12-section-kicker">LOAD / CAPACITY</div>{plan.routes.map((route) => {
    const vehicle = scenario.vehicles.find((item) => item.id === route.vehicle_id);
    const points = route.stops.map((stop) => `${scaleTime(stop.depart, scenario.start_time, end)},${100 - (stop.load_after / (vehicle?.capacity || 1)) * 100}`).join(" ");
    return <div className="p12-load-row" key={route.vehicle_id}><span>{route.vehicle_id}</span><svg viewBox="0 0 100 100" preserveAspectRatio="none"><line x1="0" y1="0" x2="100" y2="0" className="p12-capacity" /><polyline points={points} className="p12-load-line" style={{ stroke: vehicleRouteColor(route.vehicle_id, scenario.vehicles.map((item) => item.id)) }} /></svg><span>{vehicle?.capacity ?? 0}</span></div>;
  })}</div>;
}

function StopTable({ plan, scenario }: { plan: Plan; scenario: Scenario }) {
  const [sort, setSort] = useState<"arrival" | "load_after">("arrival");
  const rows = useMemo(() => plan.routes.flatMap((route) => route.stops.filter((stop) => stop.delivery_id).map((stop) => ({ ...stop, vehicle_id: route.vehicle_id }))).sort((a, b) => a[sort] - b[sort]), [plan, sort]);
  return <section className="p12-panel"><div className="p12-panel-heading"><div><h2>Stop schedule</h2><p>Exact simulator timings for every planned delivery.</p></div><label>Sort <select value={sort} onChange={(event) => setSort(event.target.value as typeof sort)}><option value="arrival">Arrival</option><option value="load_after">Load</option></select></label></div><div className="p12-table-wrap"><table><thead><tr><th>Delivery</th><th>Vehicle</th><th>Location</th><th>Arrival</th><th>Wait</th><th>Start</th><th>Depart</th><th>Load</th></tr></thead><tbody>{rows.map((stop) => <tr key={stop.delivery_id} onMouseEnter={() => sessionStore.setHovered(stop.delivery_id ?? null)} onMouseLeave={() => sessionStore.setHovered(null)}><td><b>{stop.delivery_id}</b></td><td>{stop.vehicle_id}</td><td>{stop.location_id}</td><td>{minutes(stop.arrival)}</td><td>{stop.wait}m</td><td>{minutes(stop.service_start)}</td><td>{minutes(stop.depart)}</td><td>{stop.load_after}</td></tr>)}</tbody></table></div></section>;
}

function Unplaced({ plan }: { plan: Plan }) {
  return <section className="p12-panel"><div className="p12-panel-heading"><div><h2>Unplaced deliveries</h2><p>Every unplaced delivery includes a reason from the engine.</p></div></div>{plan.unplaced.length ? plan.unplaced.map((item) => <article className="p12-unplaced" key={item.delivery_id}><b>{item.delivery_id}</b><span>{item.earliest_feasible_eta ? `Earliest feasible ETA ${minutes(item.earliest_feasible_eta)}` : "No feasible ETA found"}</span><ul>{item.reasons.map((reason) => <li key={`${item.delivery_id}-${reason.code}`}>{reason.detail}</li>)}</ul></article>) : <div className="p12-empty"><CheckCircle2 /> All deliveries placed in the current plan.</div>}</section>;
}

function DiffTable({ diff }: { diff: Diff }) {
  const [filter, setFilter] = useState<"all" | Diff["rows"][number]["classification"]>("all");
  const rows = diff.rows.filter((row) => filter === "all" || row.classification === filter);
  return <section className="p12-panel"><div className="p12-panel-heading"><div><h2>Impact diff</h2><p>Every delivery is classified with a deterministic reason.</p></div><div className="p12-filter-chips">{(["all", "kept", "moved", "broken"] as const).map((item) => <button key={item} className={filter === item ? "selected" : ""} onClick={() => setFilter(item)}>{item} {item === "all" ? diff.rows.length : diff[`${item}_count` as "kept_count" | "moved_count" | "broken_count"]}</button>)}</div></div><div className="p12-table-wrap"><table><thead><tr><th>Delivery</th><th>Status</th><th>Before → after</th><th>Reason</th></tr></thead><tbody>{rows.map((row) => <tr key={row.delivery_id} onMouseEnter={() => sessionStore.setHovered(row.delivery_id)} onMouseLeave={() => sessionStore.setHovered(null)}><td><b>{row.delivery_id}</b>{row.badge && <small className="p12-new-badge">{row.badge}</small>}</td><td><span className={`p12-classification ${row.classification}`}>{row.classification}</span></td><td>{row.before_vehicle_id ?? "—"} → {row.after_vehicle_id ?? "—"}<br /><small>{minutes(row.before_eta)} → {minutes(row.after_eta)}</small></td><td>{row.sentence}{row.classification === "broken" && row.earliest_feasible_eta != null && <small className="p12-earliest">Earliest feasible ETA {minutes(row.earliest_feasible_eta)}</small>}</td></tr>)}</tbody></table></div></section>;
}

function CompareView({ before, after }: { before: Plan; after: Plan }) {
  const routeStops = (plan: Plan) => plan.routes.flatMap((route) => route.stops.filter((stop) => stop.delivery_id).map((stop) => `${route.vehicle_id}: ${stop.delivery_id} @ ${minutes(stop.service_start)}`));
  return <section className="p12-panel"><div className="p12-panel-heading"><div><h2>Plan comparison</h2><p>Original and revised plans share the same timing language.</p></div><span className="p12-neutral-badge">GHOST STOPS SHOWN IN OUTLINE</span></div><div className="p12-compare"><div><h3>Original <small>{before.version_id}</small></h3>{routeStops(before).map((item) => <div className="p12-compare-stop ghost" key={item}>{item}</div>)}</div><div><h3>Revised <small>{after.version_id}</small></h3>{routeStops(after).map((item) => <div className="p12-compare-stop" key={item}>{item}</div>)}</div></div></section>;
}

function VerifyPanel({ report, onValidate }: { report: { passed: boolean; checks: { id: string; passed: boolean; details: string }[] }; onValidate: () => void }) {
  return <section className="p12-panel p12-verify"><div className="p12-panel-heading"><div><h2>{report.passed ? <CheckCircle2 /> : <XCircle />} Verify I1–I12</h2><p>Independent checks run on the currently displayed plan.</p></div><button className="p12-small-button" onClick={onValidate}>Re-validate</button></div><div className="p12-check-grid">{report.checks.map((check) => <div className={check.passed ? "check-ok" : "check-bad"} key={check.id}><b>{check.passed ? "✓" : "!"} {check.id}</b><span>{check.details}</span></div>)}</div>{!report.passed && <div className="p12-error-banner">Plan discarded: validation failed</div>}</section>;
}

function Limits() {
  return <section className="p12-panel p12-limits"><h2>Method & limits</h2><p>The planner pre-screens impossible deliveries, constructs a deterministic regret-2 plan, improves it within a bounded budget, and validates every output before the confirm gate can commit it.</p><div className="p12-limit-columns"><div><h3>Assumptions</h3><ul><li>D1: integer minutes since midnight</li><li>D2: matrix travel times are authoritative</li><li>D3: hard capacity and delivery windows</li><li>D4: exact-match names only</li><li>D5: one disruption per report</li></ul></div><div><h3>Measured evidence</h3><p>Fuzz cases: <b>pending</b></p><p>Optimality gap: <b>pending</b></p><p>Performance benchmark: <b>pending</b></p></div></div></section>;
}

function HighlightedText({ proposal }: { proposal: Proposal }) {
  const text = proposal.original_text;
  if (!text) return null;
  const spans = [...proposal.spans].sort((a, b) => a.start - b.start);
  const parts: ReactNode[] = [];
  let cursor = 0;
  spans.forEach((span, index) => {
    if (span.start > cursor) parts.push(<span key={`plain-${index}`}>{text.slice(cursor, span.start)}</span>);
    parts.push(<mark key={`${span.field}-${index}`} title={span.field}>{text.slice(span.start, span.end)}</mark>);
    cursor = span.end;
  });
  parts.push(<span key="plain-end">{text.slice(cursor)}</span>);
  return <div className="p12-source-text"><b>Parsed report</b><span>{parts}</span></div>;
}

function DisruptionConsole({ scenario, onResult, onPendingChange }: { scenario: Scenario; onResult: (result: { proposal: Proposal; revised?: Plan; diff?: Diff }) => void; onPendingChange: (pending: boolean) => void }) {
  const [tab, setTab] = useState<"form" | "text">("form");
  const [kind, setKind] = useState<"road_closure" | "vehicle_failure" | "urgent_delivery">("road_closure");
  const [from, setFrom] = useState(scenario.locations[1]?.id ?? scenario.depot_id);
  const [to, setTo] = useState(scenario.locations[2]?.id ?? scenario.depot_id);
  const [vehicle, setVehicle] = useState(scenario.vehicles[0]?.id ?? "");
  const [text, setText] = useState("");
  const [proposal, setProposal] = useState<Proposal>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const locationOptions = scenario.locations.map((location) => <option key={location.id} value={location.id}>{location.name} ({location.id})</option>);
  const submit = async () => {
    setBusy(true); setError("");
    try {
      const next = tab === "text" ? await api.interpret(text) : await api.preview(kind === "road_closure" ? { type: "road_closure", a: from, b: to, mode: "add_minutes", value: 20, both_directions: true, start: scenario.now, end: scenario.now + 120 } : kind === "vehicle_failure" ? { type: "vehicle_failure", vehicle_id: vehicle, at_time: scenario.now + 30, transfer_minutes: 10 } : { type: "urgent_delivery", report_time: scenario.now, priority: 2, delivery: { id: `NEW-${Date.now()}`, location_id: from, demand: 1, window_open: scenario.now, window_close: scenario.now + 240, service_time: 5, priority: 2, release_time: scenario.now } });
      setProposal(next); onPendingChange(next.status === "pending"); onResult({ proposal: next });
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : "The report could not be interpreted.";
      setError(message);
    } finally { setBusy(false); }
  };
  const confirm = async () => { if (!proposal || proposal.rejections.length) return; setBusy(true); try { const result = await api.confirm(proposal.id); setProposal({ ...proposal, status: "confirmed" }); onPendingChange(false); onResult({ proposal: { ...proposal, status: "confirmed" }, revised: result.plan, diff: result.diff }); } catch (reason) { setError(reason instanceof Error ? reason.message : "Confirmation failed."); } finally { setBusy(false); } };
  return <section className="p12-panel p12-disruption"><div className="p12-panel-heading"><div><h2>Disruption console</h2><p>Preview first; only a confirmed proposal can change the plan.</p></div><span className="p12-neutral-badge">SERVER GATE ENABLED</span></div><div className="p12-tabs"><button className={tab === "form" ? "selected" : ""} onClick={() => setTab("form")}>Form</button><button className={tab === "text" ? "selected" : ""} onClick={() => setTab("text")}>Text report</button></div>{tab === "form" ? <div className="p12-form-grid"><label>Event<select value={kind} onChange={(event) => setKind(event.target.value as typeof kind)}><option value="road_closure">Road closure</option><option value="vehicle_failure">Vehicle failure</option><option value="urgent_delivery">Urgent delivery</option></select></label>{kind === "vehicle_failure" ? <label>Vehicle<select value={vehicle} onChange={(event) => setVehicle(event.target.value)}>{scenario.vehicles.map((item) => <option key={item.id}>{item.id}</option>)}</select></label> : <><label>Location A<select value={from} onChange={(event) => setFrom(event.target.value)}>{locationOptions}</select></label>{kind === "road_closure" && <label>Location B<select value={to} onChange={(event) => setTo(event.target.value)}>{locationOptions}</select></label>}</>}<button className="p12-primary-button" onClick={submit} disabled={busy}>{busy ? "Working…" : "Preview impact"}</button></div> : <div className="p12-text-form"><textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="Example: Van 2 broke down at Cedar at 10:30" rows={3} /><button className="p12-primary-button" onClick={submit} disabled={busy || !text.trim()}>Interpret report</button></div>}{error && <div className="p12-error-banner">{error}</div>}{proposal && <div className="p12-confirm-card"><div><b>{proposal.status === "pending" ? "Pending confirmation" : "Confirmed"}</b><span>{proposal.original_text ?? `${String(proposal.disruption.type)} proposal`}</span></div><HighlightedText proposal={proposal} />{proposal.assumptions.length > 0 && <div className="p12-assumptions"><b>Assumptions</b>{proposal.assumptions.map((item) => <span key={item}>{item}</span>)}</div>}{proposal.rejections.length > 0 && <div className="p12-rejections"><b>Rejected</b>{proposal.rejections.map((item) => <span key={item}>{item}</span>)}</div>}{proposal.impact_preview && <div className="p12-preview-counts">Preview: {proposal.impact_preview.diff.kept_count} kept · {proposal.impact_preview.diff.moved_count} moved · {proposal.impact_preview.diff.broken_count} broken</div>}<div className="p12-confirm-actions"><button className="p12-primary-button" disabled={busy || proposal.status !== "pending" || proposal.rejections.length > 0} onClick={confirm}>Confirm proposal</button><button className="p12-small-button" onClick={() => { void api.discard(proposal.id); setProposal(undefined); onPendingChange(false); }}>Discard</button></div></div>}</section>;
}

type SectionId = "overview" | "disruptions" | "live-plan" | "schedule" | "compare" | "verify" | "method";

const sections: { id: SectionId; label: string; description: string; icon: typeof LayoutDashboard }[] = [
  { id: "overview", label: "Overview", description: "Fleet and plan summary", icon: LayoutDashboard },
  { id: "disruptions", label: "Disruptions", description: "Review proposed changes", icon: Siren },
  { id: "live-plan", label: "Live plan", description: "Simulation and route map", icon: Radio },
  { id: "schedule", label: "Schedule", description: "Stops and unplaced deliveries", icon: CalendarDays },
  { id: "compare", label: "Compare", description: "Original and revised plans", icon: GitCompare },
  { id: "verify", label: "Verify", description: "Plan invariants and checks", icon: ShieldCheck },
  { id: "method", label: "Method & limits", description: "Methodology and assumptions", icon: BookOpenText },
];

function SectionHeading({ id, eyebrow, title, description }: { id: string; eyebrow: string; title: string; description: string }) {
  return (
    <div className="rr-section-heading">
      <div>
        <p className="p12-kicker">{eyebrow}</p>
        <h1 id={id}>{title}</h1>
        <p>{description}</p>
      </div>
    </div>
  );
}

function App() {
  const [scenarioName, setScenarioName] = useState("baseline");
  const { data, error, loading } = useInitialPlan(scenarioName);
  const [scenarios, setScenarios] = useState<string[]>(["baseline", "impossible", "stress"]);
  const [revised, setRevised] = useState<Plan>();
  const [diff, setDiff] = useState<Diff>();
  const [activeReport, setActiveReport] = useState<{ passed: boolean; checks: { id: string; passed: boolean; details: string }[] }>();
  const [city, setCity] = useState<CityMap>();
  const [clock, setClock] = useState(480);
  const [playing, setPlaying] = useState(false);
  const [activeClosure, setActiveClosure] = useState<{ fromLocationId: string; toLocationId: string; label: string }[]>([]);
  const [activeFailures, setActiveFailures] = useState<Record<string, number>>({});
  const [selectedVehicle, setSelectedVehicle] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<SectionId>("overview");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [pendingProposal, setPendingProposal] = useState(false);
  const mobileNavTriggerRef = useRef<HTMLButtonElement>(null);
  const mobileNavCloseRef = useRef<HTMLButtonElement>(null);
  const wasMobileNavOpen = useRef(false);
  useEffect(() => {
    if (mobileNavOpen) mobileNavCloseRef.current?.focus();
    else if (wasMobileNavOpen.current) mobileNavTriggerRef.current?.focus();
    wasMobileNavOpen.current = mobileNavOpen;
  }, [mobileNavOpen]);
  useEffect(() => {
    if (!mobileNavOpen) return undefined;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileNavOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mobileNavOpen]);
  useEffect(() => { api.scenarios().then((items) => setScenarios(items.map((item) => item.name))).catch(() => undefined); }, []);
  useEffect(() => { fetch("/city_map.json").then((response) => response.json() as Promise<CityMap>).then(setCity).catch(() => undefined); }, []);
  const loadedPlan = data ? (revised ?? data.plan) : undefined;
  const end = loadedPlan && data ? Math.max(data.scenario.start_time + 60, ...loadedPlan.routes.flatMap((route) => route.stops.map((stop) => stop.depart + 20))) : 0;
  useEffect(() => { if (data) { setClock(data.scenario.now); setPlaying(false); setSelectedVehicle(null); } }, [data?.scenario.name, data?.scenario.now]);
  useEffect(() => {
    if (!playing || !end) return undefined;
    const timer = window.setInterval(() => setClock((value) => {
      if (value >= end) { setPlaying(false); return end; }
      return Math.min(end, value + 1);
    }), 300);
    return () => window.clearInterval(timer);
  }, [end, playing]);
  const { hoveredDelivery } = useSessionStore();
  if (loading) return <div className="p12-state"><RefreshCw className="p12-spin" /><h1>Loading plan</h1><p>Reading the deterministic engine…</p></div>;
  if (error || !data) return <div className="p12-state p12-error"><AlertCircle /><h1>Plan unavailable</h1><p>{error?.message ?? "The API did not return a plan."}</p><button onClick={() => window.location.reload()}>Retry</button></div>;
  const { scenario, plan, report } = data;
  const displayedPlan = revised ?? plan;
  const totalTravel = plan.routes.reduce((sum, route) => sum + route.total_travel, 0);
  const totalWait = plan.routes.reduce((sum, route) => sum + route.total_wait, 0);
  const mapRoutes = city ? toMapRoutes(displayedPlan, scenario) : [];
  const baselineRoutes = city && diff ? toMapRoutes(plan, scenario) : undefined;
  const stopStatus = Object.fromEntries((diff?.rows ?? []).map((row) => [row.delivery_id, row.classification]));
  const newKeys = diff?.rows.filter((row) => row.badge === "NEW").map((row) => row.delivery_id) ?? [];
  const unplacedLocationIds = displayedPlan.unplaced.map((item) => scenario.deliveries.find((delivery) => delivery.id === item.delivery_id)?.location_id).filter((id): id is string => Boolean(id));
  const validation = activeReport ?? report;
  const planStatus = validation.passed ? "Validated" : "Validation failed";
  const navBadge = (id: SectionId) => id === "disruptions"
    ? Number(pendingProposal)
    : id === "schedule" ? displayedPlan.unplaced.length : 0;
  const selectSection = (id: SectionId) => {
    setActiveSection(id);
    setMobileNavOpen(false);
  };
  const onValidate = () => { void api.validate(displayedPlan).then(setActiveReport); };

  return (
    <div className="rr-shell">
      {mobileNavOpen && <button className="rr-nav-backdrop" aria-label="Close navigation" onClick={() => setMobileNavOpen(false)} />}
      <aside id="rr-primary-navigation" className={`rr-sidebar ${mobileNavOpen ? "is-open" : ""}`} aria-label="Primary navigation">
        <div className="rr-sidebar-brand">
          <span className="p12-brand-mark"><Route size={18} /></span>
          <span>ReRoute</span>
          <button ref={mobileNavCloseRef} className="rr-mobile-close" aria-label="Close navigation" onClick={() => setMobileNavOpen(false)}><X size={18} /></button>
        </div>
        <p className="rr-sidebar-label">DISPATCH WORKSPACE</p>
        <nav className="rr-sidebar-nav" aria-label="Sections">
          {sections.map(({ id, label, description, icon: Icon }) => {
            const badge = navBadge(id);
            return (
              <button
                key={id}
                type="button"
                className={`rr-nav-item ${activeSection === id ? "is-active" : ""}`}
                aria-current={activeSection === id ? "page" : undefined}
                aria-label={badge ? `${label}, ${badge}` : label}
                title={description}
                onClick={() => selectSection(id)}
              >
                <Icon size={18} aria-hidden="true" />
                <span className="rr-nav-label">{label}</span>
                {badge > 0 && <span className="rr-nav-badge">{badge}</span>}
              </button>
            );
          })}
        </nav>
        <div className="rr-sidebar-foot"><span className="rr-status-dot" /> LOCAL SIMULATION</div>
      </aside>

      <div className="rr-workspace">
        <header className="rr-topbar">
          <button ref={mobileNavTriggerRef} className="rr-mobile-menu" aria-label="Open navigation" aria-expanded={mobileNavOpen} aria-controls="rr-primary-navigation" onClick={() => setMobileNavOpen(true)}><Menu size={19} /></button>
          <div className="rr-mobile-brand"><span className="p12-brand-mark"><Route size={16} /></span><b>ReRoute</b></div>
          <label className="p12-scenario">Scenario
            <select value={scenarioName} onChange={(event) => { setScenarioName(event.target.value); setRevised(undefined); setDiff(undefined); setActiveClosure([]); setActiveFailures({}); }}>
              {scenarios.map((name) => <option key={name}>{name}</option>)}
            </select>
          </label>
          <span className="rr-plan-version" title={displayedPlan.version_id}>PLAN <b>{displayedPlan.version_id.slice(0, 8)}</b></span>
          <span className={`rr-validation-state ${validation.passed ? "is-valid" : "is-invalid"}`} role="status">
            {validation.passed ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}{planStatus}
          </span>
          <span className="p12-header-clock"><Clock3 size={15} /> <span>SIM TIME</span> <b>{minutes(clock)}</b></span>
          <span className="p12-mode"><i /> REAL API · OFFLINE DATA</span>
        </header>

        <main className="rr-main">
          <section className="rr-section" hidden={activeSection !== "overview"} aria-labelledby="overview-title">
            <div className="p12-title">
              <div className="p12-hero-copy">
                <p className="p12-kicker">{revised ? "REVISED PLAN" : "INITIAL PLAN"} · {scenario.name.toUpperCase()}</p>
                <h1 id="overview-title">Dispatch board</h1>
                <p>Deterministic fleet plan with timing, capacity, and feasibility evidence.</p>
              </div>
              <div className={`p12-validation ${validation.passed ? "ok" : "bad"}`}>{validation.passed ? <CheckCircle2 /> : <AlertCircle />} {planStatus}</div>
              <svg className="p12-hero-art" viewBox="0 0 420 160" aria-hidden="true">
                <circle cx="325" cy="54" r="47" fill="#c9c0f5" />
                <path d="M214 132h206v28H214zm12-34h21v34h-21zm27-16h34v50h-34zm42 24h24v26h-24zm31-32h32v58h-32zm40 20h19v38h-19z" fill="#2926c8" />
                <path d="M0 145h420M82 136c20-34 41-40 62-39-12-8-27-11-43-8 21-11 43-10 62-2-21-3-39 7-55 25" fill="none" stroke="#7669e8" strokeWidth="4" strokeLinecap="round" />
              </svg>
            </div>
            <section className="p12-kpis" aria-label="Plan metrics">
              <Kpi label="Deliveries planned" value={`${scenario.deliveries.length - displayedPlan.unplaced.length}/${scenario.deliveries.length}`} note={`${displayedPlan.unplaced.length} unplaced`} icon={<Truck />} />
              <Kpi label="Vehicles active" value={`${displayedPlan.routes.length}`} note={`${scenario.vehicles.length} available`} icon={<Route />} />
              <Kpi label="Travel time" value={`${displayedPlan.routes.reduce((sum, route) => sum + route.total_travel, 0) || totalTravel} min`} note="Matrix travel" icon={<Map />} />
              <Kpi label="Waiting time" value={`${displayedPlan.routes.reduce((sum, route) => sum + route.total_wait, 0) || totalWait} min`} note="Window waiting" icon={<Clock3 />} />
            </section>
            <div className="rr-overview-links">
              <button type="button" onClick={() => selectSection("live-plan")}><Radio size={16} /> Open live plan</button>
              <button type="button" onClick={() => selectSection("disruptions")}><Siren size={16} /> Review disruptions</button>
            </div>
          </section>

          <section className="rr-section" hidden={activeSection !== "disruptions"} aria-labelledby="disruptions-title">
            <SectionHeading id="disruptions-title" eyebrow="DISPATCH WORKSPACE" title="Disruptions" description="Interpret, preview, then confirm a proposed plan change." />
            <DisruptionConsole
              scenario={scenario}
              onPendingChange={setPendingProposal}
              onResult={(result) => {
                if (result.proposal.status !== "confirmed") return;
                setRevised(result.revised);
                setDiff(result.diff);
                setActiveReport(result.proposal.impact_preview?.validation_report);
                const disruption = result.proposal.disruption;
                if (disruption.type === "road_closure") setActiveClosure([{ fromLocationId: String(disruption.a ?? ""), toLocationId: String(disruption.b ?? ""), label: "Road closure" }]);
                if (disruption.type === "vehicle_failure") setActiveFailures({ [String(disruption.vehicle_id ?? "")]: Number(disruption.at_time ?? scenario.now) });
              }}
            />
          </section>

          <section className="rr-section" hidden={activeSection !== "live-plan"} aria-labelledby="live-plan-title">
            <SectionHeading id="live-plan-title" eyebrow="SIMULATED FLEET" title="Live plan" description="Advance the shared simulation clock to inspect route progress, stops, and vehicle loads." />
            <SimulationClock clock={clock} start={scenario.start_time} end={end} playing={playing} onClock={setClock} onPlaying={setPlaying} onReset={() => { setPlaying(false); setClock(scenario.now); }} />
            <div className="p12-grid rr-live-grid">
              <section className="p12-panel p12-gantt-panel">
                <div className="p12-panel-heading">
                  <div><h2>Vehicle timelines</h2><p>Service blocks, delivery windows, and the shared current-time marker.</p></div>
                  <span className="p12-now-key">NOW {minutes(clock)}</span>
                </div>
                <Gantt plan={displayedPlan} scenario={scenario} clock={clock} />
                <LoadProfile plan={displayedPlan} scenario={scenario} />
              </section>
              {city
                ? <ScheduleMap city={city} routes={mapRoutes} clock={clock} baselineRoutes={baselineRoutes} failures={activeFailures} closures={activeClosure} stopStatus={stopStatus} newKeys={newKeys} vehicleIds={scenario.vehicles.map((vehicle) => vehicle.id)} unplacedLocationIds={unplacedLocationIds} highlightedKey={hoveredDelivery} selectedVehicleId={selectedVehicle} onHoverStop={(key) => sessionStore.setHovered(key)} onSelectVehicle={setSelectedVehicle} />
                : <section className="p12-panel p12-map-panel"><div className="p12-panel-heading"><h2>Loading schematic map</h2></div></section>}
            </div>
          </section>

          <section className="rr-section" hidden={activeSection !== "schedule"} aria-labelledby="schedule-title">
            <SectionHeading id="schedule-title" eyebrow="DELIVERY OPERATIONS" title="Schedule" description="Planned stops, service timing, and deliveries that could not be placed." />
            <div className="rr-schedule-grid">
              <StopTable plan={displayedPlan} scenario={scenario} />
              <Unplaced plan={displayedPlan} />
            </div>
          </section>

          <section className="rr-section" hidden={activeSection !== "compare"} aria-labelledby="compare-title">
            <SectionHeading id="compare-title" eyebrow="PLAN CHANGES" title="Compare" description="Inspect the original plan, revised assignments, and the reason for every change." />
            {diff
              ? <><CompareView before={plan} after={displayedPlan} /><DiffTable diff={diff} /></>
              : <div className="rr-empty-state"><GitCompare size={22} /><b>No revised plan to compare</b><span>Preview and confirm a disruption to see the original and revised plans here.</span><button type="button" className="p12-primary-button" onClick={() => selectSection("disruptions")}>Go to disruptions</button></div>}
          </section>

          <section className="rr-section" hidden={activeSection !== "verify"} aria-labelledby="verify-title">
            <SectionHeading id="verify-title" eyebrow="PLAN SAFETY" title="Verify" description="Independent validation results for the currently displayed plan." />
            <VerifyPanel report={validation} onValidate={onValidate} />
          </section>

          <section className="rr-section" hidden={activeSection !== "method"} aria-labelledby="method-title">
            <SectionHeading id="method-title" eyebrow="HOW THE PLAN IS BUILT" title="Method & limits" description="A transparent heuristic with explicit operational assumptions and measured evidence." />
            <Limits />
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;
