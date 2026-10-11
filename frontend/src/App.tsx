import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import {
  AlertCircle,
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
  const vehicleIds = scenario.vehicles.map((vehicle) => vehicle.id);
  return <div className="p12-gantt">
    <div className="p12-stop-order-heading"><span>VEHICLE</span><span>DELIVERY STOPS IN ROUTE ORDER <small>· start time shown on each stop</small></span></div>
    {plan.routes.map((route) => {
      const vehicle = scenario.vehicles.find((item) => item.id === route.vehicle_id);
      const deliveryStops = route.stops.filter((stop) => stop.delivery_id);
      const routeColor = vehicleRouteColor(route.vehicle_id, vehicleIds);
      return <div className="p12-route-row" key={route.vehicle_id}>
        <div className="p12-route-label">
          <span className="p12-route-dot" style={{ background: routeColor }} />
          <div><b>{route.vehicle_id}</b><span>{vehicle?.name ?? "Vehicle"}</span></div>
        </div>
        <div className="p12-stop-sequence">
          {deliveryStops.length ? deliveryStops.map((stop, stopIndex) => (
            <Fragment key={`${route.vehicle_id}-${stop.delivery_id}-${stopIndex}`}>
              {stopIndex > 0 && <span className="p12-stop-connector" aria-hidden="true" />}
              <button
                type="button"
                className={`p12-stop-card ${stop.wait ? "has-wait" : ""} ${hoveredDelivery === stop.delivery_id ? "is-highlighted" : ""}`}
                style={{ "--route-color": routeColor } as CSSProperties}
                onMouseEnter={() => sessionStore.setHovered(stop.delivery_id ?? null)}
                onMouseLeave={() => sessionStore.setHovered(null)}
                title={`${stop.delivery_id} · ${stop.location_id} · arrival ${minutes(stop.arrival)} · start ${minutes(stop.service_start)} · depart ${minutes(stop.depart)}`}
              >
                <span className="p12-stop-card-index">{stopIndex + 1}</span>
                <span className="p12-stop-card-main"><b>{stop.delivery_id}</b><span>{stop.location_id}</span></span>
                <span className="p12-stop-card-time">{minutes(stop.service_start)}</span>
                {stop.wait > 0 && <span className="p12-stop-wait">Wait {stop.wait}m</span>}
              </button>
            </Fragment>
          )) : <span className="p12-no-stops">No delivery stops assigned</span>}
        </div>
      </div>;
    })}
    <div className="p12-axis-footer"><span>Stops read left to right · start times shown in each card · simulation now {minutes(clock)}</span></div>
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

function LoadProfile({ plan, scenario, clock }: { plan: Plan; scenario: Scenario; clock: number }) {
  return <div className="p12-loads"><div className="p12-section-kicker">CURRENT LOAD AT {minutes(clock)}</div>{plan.routes.map((route) => {
    const vehicle = scenario.vehicles.find((item) => item.id === route.vehicle_id);
    const completedStop = route.stops.filter((stop) => stop.depart <= clock).at(-1);
    const depotStart = route.stops.find((stop) => stop.kind === "depot_start");
    const load = completedStop?.load_after ?? depotStart?.load_after ?? 0;
    const capacity = vehicle?.capacity ?? 0;
    const percent = capacity ? Math.min(100, (load / capacity) * 100) : 0;
    return <div className="p12-load-row" key={route.vehicle_id}>
      <span className="p12-load-vehicle">{route.vehicle_id}</span>
      <div className="p12-load-meter" role="meter" aria-label={`${route.vehicle_id} current load`} aria-valuenow={load} aria-valuemin={0} aria-valuemax={capacity}>
        <div style={{ width: `${percent}%`, background: vehicleRouteColor(route.vehicle_id, scenario.vehicles.map((item) => item.id)) }} />
      </div>
      <span className="p12-load-value">{load}<small> / {capacity}</small></span>
    </div>;
  })}</div>;
}

function timeToMinutes(value: string) {
  const [hours, minutes] = value.split(":").map(Number);
  return (hours ?? 0) * 60 + (minutes ?? 0);
}

function StopTable({ plan, scenario }: { plan: Plan; scenario: Scenario }) {
  const [sort, setSort] = useState<"arrival" | "load_after">("arrival");
  const [showForm, setShowForm] = useState(false);
  const [manualTrips, setManualTrips] = useState<Array<{
    delivery_id: string;
    vehicle_id: string;
    location_id: string;
    arrival: number;
    wait: number;
    service_start: number;
    depart: number;
    load_after: number;
  }>>([]);
  const [form, setForm] = useState({
    delivery_id: "",
    vehicle_id: scenario.vehicles[0]?.id ?? "",
    location_id: scenario.locations[0]?.id ?? "",
    start: "08:00",
    depart: "08:30",
    load: "1",
  });

  const scheduledRows = useMemo(() => {
    const baseRows = plan.routes.flatMap((route) => route.stops.filter((stop) => stop.delivery_id).map((stop) => ({ ...stop, vehicle_id: route.vehicle_id })));
    return [...baseRows, ...manualTrips];
  }, [manualTrips, plan.routes]);

  const rows = useMemo(() => scheduledRows.sort((a, b) => a[sort] - b[sort]), [scheduledRows, sort]);

  const addTrip = (event: React.FormEvent) => {
    event.preventDefault();
    if (!form.delivery_id.trim() || !form.vehicle_id || !form.location_id) return;
    const startMinutes = timeToMinutes(form.start);
    const departMinutes = timeToMinutes(form.depart);
    if (Number.isNaN(startMinutes) || Number.isNaN(departMinutes) || departMinutes < startMinutes) return;

    setManualTrips((current) => [
      ...current,
      {
        delivery_id: form.delivery_id.trim(),
        vehicle_id: form.vehicle_id,
        location_id: form.location_id,
        arrival: startMinutes,
        wait: 0,
        service_start: startMinutes,
        depart: departMinutes,
        load_after: Number(form.load) || 0,
      },
    ]);
    setForm({
      delivery_id: "",
      vehicle_id: scenario.vehicles[0]?.id ?? "",
      location_id: scenario.locations[0]?.id ?? "",
      start: form.start,
      depart: form.depart,
      load: "1",
    });
    setShowForm(false);
  };

  return <section className="p12-panel"><div className="p12-panel-heading"><div><h2>Stop schedule</h2><p>Exact simulator timings for every planned delivery.</p></div><div style={{ display: "flex", alignItems: "center", gap: 8 }}><button type="button" onClick={() => setShowForm((open) => !open)} className="p12-small-button">{showForm ? "Close" : "Create trip"}</button><label>Sort <select value={sort} onChange={(event) => setSort(event.target.value as typeof sort)}><option value="arrival">Arrival</option><option value="load_after">Load</option></select></label></div></div>
    {showForm && <form onSubmit={addTrip} style={{ display: "grid", gridTemplateColumns: "repeat(6, minmax(120px, 1fr))", gap: 10, padding: "0 18px 18px", borderBottom: "1px solid #edf1ed" }}>
      <label style={{ display: "grid", gap: 6, color: "#66736b", fontSize: 11, fontWeight: 700 }}>
        Delivery ID
        <input value={form.delivery_id} onChange={(event) => setForm((current) => ({ ...current, delivery_id: event.target.value }))} style={{ padding: "8px 10px", border: "1px solid #dfe7e1", borderRadius: 6 }} placeholder="D101" />
      </label>
      <label style={{ display: "grid", gap: 6, color: "#66736b", fontSize: 11, fontWeight: 700 }}>
        Vehicle
        <select value={form.vehicle_id} onChange={(event) => setForm((current) => ({ ...current, vehicle_id: event.target.value }))} style={{ padding: "8px 10px", border: "1px solid #dfe7e1", borderRadius: 6 }}>
          {scenario.vehicles.map((vehicle) => <option key={vehicle.id} value={vehicle.id}>{vehicle.id}</option>)}
        </select>
      </label>
      <label style={{ display: "grid", gap: 6, color: "#66736b", fontSize: 11, fontWeight: 700 }}>
        Location
        <select value={form.location_id} onChange={(event) => setForm((current) => ({ ...current, location_id: event.target.value }))} style={{ padding: "8px 10px", border: "1px solid #dfe7e1", borderRadius: 6 }}>
          {scenario.locations.map((location) => <option key={location.id} value={location.id}>{location.name}</option>)}
        </select>
      </label>
      <label style={{ display: "grid", gap: 6, color: "#66736b", fontSize: 11, fontWeight: 700 }}>
        Start
        <input type="time" value={form.start} onChange={(event) => setForm((current) => ({ ...current, start: event.target.value }))} style={{ padding: "8px 10px", border: "1px solid #dfe7e1", borderRadius: 6 }} />
      </label>
      <label style={{ display: "grid", gap: 6, color: "#66736b", fontSize: 11, fontWeight: 700 }}>
        Depart
        <input type="time" value={form.depart} onChange={(event) => setForm((current) => ({ ...current, depart: event.target.value }))} style={{ padding: "8px 10px", border: "1px solid #dfe7e1", borderRadius: 6 }} />
      </label>
      <label style={{ display: "grid", gap: 6, color: "#66736b", fontSize: 11, fontWeight: 700 }}>
        Load
        <input type="number" min={0} value={form.load} onChange={(event) => setForm((current) => ({ ...current, load: event.target.value }))} style={{ padding: "8px 10px", border: "1px solid #dfe7e1", borderRadius: 6 }} />
      </label>
      <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 4 }}>
        <button type="button" onClick={() => setShowForm(false)} className="p12-small-button">Cancel</button>
        <button type="submit" className="p12-primary-button">Add trip</button>
      </div>
    </form>}
    <div className="p12-table-wrap"><table><thead><tr><th>Delivery</th><th>Vehicle</th><th>Location</th><th>Arrival</th><th>Wait</th><th>Start</th><th>Depart</th><th>Load</th></tr></thead><tbody>{rows.map((stop) => <tr key={`${stop.delivery_id}-${stop.vehicle_id}-${stop.arrival}-${stop.depart}`} onMouseEnter={() => sessionStore.setHovered(stop.delivery_id ?? null)} onMouseLeave={() => sessionStore.setHovered(null)}><td><b>{stop.delivery_id}</b></td><td>{stop.vehicle_id}</td><td>{stop.location_id}</td><td>{minutes(stop.arrival)}</td><td>{stop.wait}m</td><td>{minutes(stop.service_start)}</td><td>{minutes(stop.depart)}</td><td>{stop.load_after}</td></tr>)}</tbody></table></div></section>;
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
  type IndexedStop = { stop: Stop & { delivery_id: string }; vehicleId: string };
  const indexStops = (plan: Plan): Map<string, IndexedStop> => new globalThis.Map(
    plan.routes.flatMap((route) => route.stops
      .filter((stop): stop is Stop & { delivery_id: string } => stop.delivery_id != null)
      .map((stop) => [stop.delivery_id, { stop, vehicleId: route.vehicle_id }] as const)),
  );
  const original = indexStops(before);
  const revised = indexStops(after);
  const deliveryIds = [...new Set([...original.keys(), ...revised.keys()])].sort();

  const renderPlanCell = (entry: IndexedStop | undefined, other: IndexedStop | undefined, side: "original" | "revised") => {
    if (!entry) return <span className="p12-compare-missing">{side === "original" ? "Not in original plan" : "Not scheduled"}</span>;
    const eta = entry.stop.service_start;
    const etaChanged = other !== undefined && eta !== other.stop.service_start;
    const className = side === "revised" && etaChanged ? (eta < other.stop.service_start ? "is-better" : "is-worse") : "";
    return <div className={`p12-compare-plan-cell ${className}`}>
      <span className="p12-compare-assignment">{entry.vehicleId} <span>·</span> {entry.stop.location_id}</span>
      <span className="p12-compare-eta">{minutes(eta)}</span>
      {entry.stop.wait > 0 && <small>Wait {entry.stop.wait}m</small>}
    </div>;
  };

  return <section className="p12-panel"><div className="p12-panel-heading"><div><h2>Plan comparison</h2><p>Rows are matched by delivery so assignment and arrival changes are easy to spot.</p></div><span className="p12-neutral-badge">EARLIER ETA = GOOD</span></div>
    <div className="p12-compare-summary"><span><i className="is-better" /> Earlier ETA</span><span><i className="is-worse" /> Later ETA</span><span><i className="is-changed" /> Assignment changed</span></div>
    <div className="p12-table-wrap p12-compare-table-wrap"><table className="p12-compare-table"><thead><tr><th>Delivery</th><th>Original plan <small>{before.version_id}</small></th><th>Revised plan <small>{after.version_id}</small></th><th>Difference</th></tr></thead><tbody>
      {deliveryIds.map((deliveryId) => {
        const oldEntry = original.get(deliveryId);
        const newEntry = revised.get(deliveryId);
        const etaDelta = oldEntry && newEntry ? newEntry.stop.service_start - oldEntry.stop.service_start : undefined;
        const assignmentChanged = Boolean(oldEntry && newEntry && oldEntry.vehicleId !== newEntry.vehicleId);
        const locationChanged = Boolean(oldEntry && newEntry && oldEntry.stop.location_id !== newEntry.stop.location_id);
        const isNew = !oldEntry && Boolean(newEntry);
        const isRemoved = Boolean(oldEntry && !newEntry);
        const differences: string[] = [];
        if (isNew) differences.push("New delivery");
        else if (isRemoved) differences.push("No longer scheduled");
        if (assignmentChanged && oldEntry && newEntry) differences.push(`Vehicle ${oldEntry.vehicleId} → ${newEntry.vehicleId}`);
        if (locationChanged && oldEntry && newEntry) differences.push("Location changed");
        if (etaDelta !== undefined && etaDelta !== 0) differences.push(`${etaDelta < 0 ? `${Math.abs(etaDelta)}m earlier` : `${etaDelta}m later`}`);
        const rowClass = isNew ? "is-new" : isRemoved ? "is-removed" : etaDelta !== undefined && etaDelta < 0 ? "is-positive" : etaDelta !== undefined && etaDelta > 0 ? "is-negative" : "";
        return <tr key={deliveryId} className={rowClass}>
          <td><b>{deliveryId}</b></td>
          <td>{renderPlanCell(oldEntry, newEntry, "original")}</td>
          <td>{renderPlanCell(newEntry, oldEntry, "revised")}</td>
          <td>{differences.length ? <span className={`p12-compare-difference ${etaDelta !== undefined && etaDelta < 0 ? "is-better" : etaDelta !== undefined && etaDelta > 0 ? "is-worse" : ""}`}>{differences.join(" · ")}</span> : <span className="p12-compare-unchanged">No change</span>}</td>
        </tr>;
      })}
    </tbody></table></div>
  </section>;
}

function VerifyPanel({ report, onValidate }: { report: { passed: boolean; checks: { id: string; passed: boolean; details: string }[] }; onValidate: () => void }) {
  return <section className="p12-panel p12-verify"><div className="p12-panel-heading"><div><h2>{report.passed ? <CheckCircle2 /> : <XCircle />} Verify I1–I12</h2><p>Independent checks run on the currently displayed plan.</p></div><button className="p12-small-button" onClick={onValidate}>Re-validate</button></div><div className="p12-check-grid">{report.checks.map((check) => <div className={check.passed ? "check-ok" : "check-bad"} key={check.id}><b>{check.passed ? "✓" : "!"} {check.id}</b><span>{check.details}</span></div>)}</div>{!report.passed && <div className="p12-error-banner">Plan discarded: validation failed</div>}</section>;
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
  const interpretationId = useRef(0);
  const callbacks = useRef({ onResult, onPendingChange });
  callbacks.current = { onResult, onPendingChange };
  const locationOptions = scenario.locations.map((location) => <option key={location.id} value={location.id}>{location.name} ({location.id})</option>);

  const interpretText = async (reportText: string) => {
    const requestId = ++interpretationId.current;
    setBusy(true);
    setError("");
    try {
      const next = await api.interpret(reportText);
      if (requestId !== interpretationId.current) {
        if (next.status === "pending") await api.discard(next.id);
        return;
      }
      setProposal(next);
      callbacks.current.onPendingChange(next.status === "pending");
      callbacks.current.onResult({ proposal: next });
    } catch (reason) {
      if (requestId === interpretationId.current) {
        setError(reason instanceof Error ? reason.message : "The report could not be interpreted.");
      }
    } finally {
      if (requestId === interpretationId.current) setBusy(false);
    }
  };

  useEffect(() => {
    if (tab !== "text" || !text.trim()) return undefined;
    const reportText = text.trim();
    const timer = window.setTimeout(() => { void interpretText(reportText); }, 650);
    return () => {
      window.clearTimeout(timer);
      interpretationId.current += 1;
    };
  }, [tab, text]);

  const updateText = (value: string) => {
    interpretationId.current += 1;
    setBusy(false);
    setError("");
    if (proposal?.source === "text" && proposal.status === "pending") {
      void api.discard(proposal.id).catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "The previous draft could not be discarded.");
      });
    }
    setProposal(undefined);
    callbacks.current.onPendingChange(false);
    setText(value);
  };

  const selectTab = (nextTab: "form" | "text") => {
    if (nextTab === tab) return;
    interpretationId.current += 1;
    setBusy(false);
    setError("");
    if (proposal?.source === "text" && proposal.status === "pending") {
      void api.discard(proposal.id).catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "The previous draft could not be discarded.");
      });
    }
    if (proposal?.source === "text") {
      setProposal(undefined);
      callbacks.current.onPendingChange(false);
    }
    setTab(nextTab);
  };

  const submit = async () => {
    if (tab === "text") {
      await interpretText(text.trim());
      return;
    }
    setBusy(true); setError("");
    try {
      const next = await api.preview(kind === "road_closure" ? { type: "road_closure", a: from, b: to, mode: "add_minutes", value: 20, both_directions: true, start: scenario.now, end: scenario.now + 120 } : kind === "vehicle_failure" ? { type: "vehicle_failure", vehicle_id: vehicle, at_time: scenario.now + 30, transfer_minutes: 10 } : { type: "urgent_delivery", report_time: scenario.now, priority: 2, delivery: { id: `NEW-${Date.now()}`, location_id: from, demand: 1, window_open: scenario.now, window_close: scenario.now + 240, service_time: 5, priority: 2, release_time: scenario.now } });
      setProposal(next); onPendingChange(next.status === "pending"); onResult({ proposal: next });
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : "The report could not be interpreted.";
      setError(message);
    } finally { setBusy(false); }
  };
  const confirm = async () => { if (!proposal || proposal.rejections.length) return; setBusy(true); try { const result = await api.confirm(proposal.id); setProposal({ ...proposal, status: "confirmed" }); onPendingChange(false); onResult({ proposal: { ...proposal, status: "confirmed" }, revised: result.plan, diff: result.diff }); } catch (reason) { setError(reason instanceof Error ? reason.message : "Confirmation failed."); } finally { setBusy(false); } };
  return <section className="p12-panel p12-disruption">
    <div className="p12-panel-heading">
      <div><h2>Disruption console</h2><p>Preview first; only a confirmed proposal can change the plan.</p></div>
      <span className="p12-neutral-badge">SERVER GATE ENABLED</span>
    </div>
    <div className="p12-tabs">
      <button className={tab === "form" ? "selected" : ""} onClick={() => selectTab("form")}>Form</button>
      <button className={tab === "text" ? "selected" : ""} onClick={() => selectTab("text")}>Text report</button>
    </div>
    {tab === "form"
      ? <div className="p12-form-grid">
          <label>Event<select value={kind} onChange={(event) => setKind(event.target.value as typeof kind)}><option value="road_closure">Road closure</option><option value="vehicle_failure">Vehicle failure</option><option value="urgent_delivery">Urgent delivery</option></select></label>
          {kind === "vehicle_failure"
            ? <label>Vehicle<select value={vehicle} onChange={(event) => setVehicle(event.target.value)}>{scenario.vehicles.map((item) => <option key={item.id}>{item.id}</option>)}</select></label>
            : <><label>Location A<select value={from} onChange={(event) => setFrom(event.target.value)}>{locationOptions}</select></label>{kind === "road_closure" && <label>Location B<select value={to} onChange={(event) => setTo(event.target.value)}>{locationOptions}</select></label>}</>}
          <button className="p12-primary-button" onClick={submit} disabled={busy}>{busy ? "Working…" : "Preview impact"}</button>
        </div>
      : <div className="p12-text-form">
          <textarea value={text} onChange={(event) => updateText(event.target.value)} placeholder="Enter a manual disruption report, e.g. Van 2 broke down at Cedar at 10:30" rows={3} aria-describedby="text-report-status" />
          <div id="text-report-status" className="p12-text-report-status" role="status">
            {busy ? "Interpreting report…" : proposal?.source === "text" ? "Report interpreted. Review the proposed changes below." : text.trim() ? "Interpreting report shortly…" : "Enter a disruption report to preview the proposed change."}
          </div>
          <button className="p12-primary-button" onClick={submit} disabled={busy || !text.trim()}>{busy ? "Interpreting…" : "Interpret report"}</button>
        </div>
    }
    {error && <div className="p12-error-banner">{error}</div>}
    {proposal && <div className="p12-confirm-card">
      <div><b>{proposal.status === "pending" ? "Pending confirmation" : "Confirmed"}</b><span>{proposal.original_text ?? `${String(proposal.disruption.type)} proposal`}</span></div>
      <HighlightedText proposal={proposal} />
      {proposal.assumptions.length > 0 && <div className="p12-assumptions"><b>Assumptions</b>{proposal.assumptions.map((item) => <span key={item}>{item}</span>)}</div>}
      {proposal.rejections.length > 0 && <div className="p12-rejections"><b>Rejected</b>{proposal.rejections.map((item) => <span key={item}>{item}</span>)}</div>}
      {proposal.impact_preview && <div className="p12-preview-counts">Preview: {proposal.impact_preview.diff.kept_count} kept · {proposal.impact_preview.diff.moved_count} moved · {proposal.impact_preview.diff.broken_count} broken</div>}
      <div className="p12-confirm-actions">
        <button className="p12-primary-button" disabled={busy || proposal.status !== "pending" || proposal.rejections.length > 0} onClick={confirm}>Confirm proposal</button>
        <button className="p12-small-button" onClick={() => { void api.discard(proposal.id); setProposal(undefined); onPendingChange(false); }}>Discard</button>
      </div>
    </div>}
  </section>;
}

type SectionId = "overview" | "disruptions" | "live-plan" | "schedule" | "compare" | "verify";

const sections: { id: SectionId; label: string; description: string; icon: typeof LayoutDashboard }[] = [
  { id: "overview", label: "Overview", description: "Fleet and plan summary", icon: LayoutDashboard },
  { id: "disruptions", label: "Disruptions", description: "Review proposed changes", icon: Siren },
  { id: "live-plan", label: "Live plan", description: "Simulation and route map", icon: Radio },
  { id: "schedule", label: "Schedule", description: "Stops and unplaced deliveries", icon: CalendarDays },
  { id: "compare", label: "Compare", description: "Original and revised plans", icon: GitCompare },
  { id: "verify", label: "Verify", description: "Plan invariants and checks", icon: ShieldCheck },
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
  const scenarioName = "baseline";
  const { data, error, loading } = useInitialPlan(scenarioName);
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
                  <div><h2>Vehicle timelines</h2><p>Follow each vehicle’s stops in route order; times and waiting are shown on every stop.</p></div>
                  <span className="p12-now-key">NOW {minutes(clock)}</span>
                </div>
                <Gantt plan={displayedPlan} scenario={scenario} clock={clock} />
                <LoadProfile plan={displayedPlan} scenario={scenario} clock={clock} />
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
        </main>
      </div>
    </div>
  );
}

export default App;
