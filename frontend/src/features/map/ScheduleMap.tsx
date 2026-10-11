import { useEffect, useMemo, useRef, useState } from 'react';
import { CityGraph, type CityMap, type Pt } from './cityGraph';
import { buildTimeline, fmtTime, loadAt, stateAt, type MapRoute, type Timeline, type VehicleState } from './timeline';
import { vehicleRouteColor } from '../../lib/routeColors';

export type DiffClass = 'kept' | 'moved' | 'broken';

// green / amber / red are reserved for kept / moved / broken, so vehicle colours avoid them.
const DIFF_COLOR: Record<DiffClass, string> = { kept: '#279B91', moved: '#A56B16', broken: '#B83F50' };

export interface ScheduleMapProps {
  city: CityMap;
  routes: MapRoute[];
  /** Simulation clock, minutes since midnight. Share it with the Gantt chart. */
  clock: number;
  /** Previous plan, drawn as faded dashed ghosts for before/after analysis. */
  baselineRoutes?: MapRoute[];
  /** vehicleId -> failure time (minutes). */
  failures?: Record<string, number>;
  /** Closed edges, given as the two locations the matrix entry joins. */
  closures?: { fromLocationId: string; toLocationId: string; label?: string }[];
  /** stop key -> diff class, from the diff table. */
  stopStatus?: Record<string, DiffClass>;
  /** Stop keys of newly reported urgent deliveries (badged NEW). */
  newKeys?: string[];
  /** All scenario vehicles, used to keep route colours stable across replans. */
  vehicleIds?: string[];
  /** Locations of deliveries that could not be placed. */
  unplacedLocationIds?: string[];
  highlightedKey?: string | null;
  selectedVehicleId?: string | null;
  onHoverStop?: (key: string | null) => void;
  onSelectVehicle?: (vehicleId: string | null) => void;
}

interface View { x: number; y: number; w: number }
const ROAD_PX = { local: 2.5, arterial: 4, bridge: 5 } as const;
const ROAD_CASING = { local: '#50577E', arterial: '#71779A', bridge: '#54DCE8' } as const;
const ROAD_FILL = { local: '#30365D', arterial: '#363D66', bridge: '#404873' } as const;

const pts = (p: Pt[]) => p.map(([x, y]) => `${x},${y}`).join(' ');

function useWidth(ref: React.RefObject<HTMLElement | null>): number {
  const [w, setW] = useState(800);
  useEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width || 800));
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, [ref]);
  return w;
}

function describe(tl: Timeline, st: VehicleState, graph: CityGraph, failedAt?: number): string {
  const stop = st.stopIdx >= 0 ? tl.route.stops[st.stopIdx] : undefined;
  const place = stop ? graph.name(stop.locationId) : '';
  switch (st.status) {
    case 'driving': return `Driving to ${place}, arrives ${fmtTime(st.until ?? 0)}`;
    case 'waiting': return `Waiting at ${place} until ${fmtTime(st.until ?? 0)}`;
    case 'servicing': return `Servicing ${place} until ${fmtTime(st.until ?? 0)}`;
    case 'failed': return `Failed at ${fmtTime(failedAt ?? 0)}`;
    default:
      if (!tl.route.stops.length) return 'No stops assigned';
      return st.until !== null ? `Departs ${fmtTime(st.until)}` : 'Route complete';
  }
}

export function ScheduleMap(props: ScheduleMapProps) {
  const {
    city, routes, clock, baselineRoutes, failures = {}, closures = [], stopStatus = {},
    newKeys = [], vehicleIds = [], unplacedLocationIds = [], highlightedKey = null, selectedVehicleId = null,
    onHoverStop, onSelectVehicle,
  } = props;

  const graph = useMemo(() => new CityGraph(city), [city]);
  const timelines = useMemo(() => routes.map((r) => buildTimeline(r, graph)), [routes, graph]);
  const ghosts = useMemo(() => (baselineRoutes ?? []).map((r) => buildTimeline(r, graph)), [baselineRoutes, graph]);
  const closurePaths = useMemo(
    () => closures.map((c) => ({ c, path: graph.path(c.fromLocationId, c.toLocationId) })),
    [closures, graph],
  );

  const colorOf = useMemo(() => {
    const ids = vehicleIds.length ? vehicleIds : [...new Set([...routes, ...(baselineRoutes ?? [])].map((r) => r.vehicleId))].sort();
    return (id: string) => vehicleRouteColor(id, ids);
  }, [routes, baselineRoutes, vehicleIds]);

  const [W, H] = city.viewBox;
  const wrapRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const width = useWidth(wrapRef);

  // ---- pan / zoom ----------------------------------------------------------
  const fit = useMemo<View>(() => {
    const all: Pt[] = [...timelines, ...ghosts].flatMap((t) => t.fullPath);
    if (!all.length) return { x: 0, y: 0, w: W };
    const xs = all.map((p) => p[0]); const ys = all.map((p) => p[1]);
    const pad = 60;
    let w = Math.max(Math.max(...xs) - Math.min(...xs) + 2 * pad, ((Math.max(...ys) - Math.min(...ys) + 2 * pad) * W) / H, 300);
    w = Math.min(w, W);
    const h = (w * H) / W;
    const cx = (Math.max(...xs) + Math.min(...xs)) / 2; const cy = (Math.max(...ys) + Math.min(...ys)) / 2;
    return { x: Math.min(Math.max(cx - w / 2, 0), W - w), y: Math.min(Math.max(cy - h / 2, 0), H - h), w };
  }, [timelines, ghosts, W, H]);
  const [view, setView] = useState<View | null>(null);
  const v = view ?? fit;
  const vh = (v.w * H) / W;
  const u = v.w / width; // map units per screen pixel

  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const r = el.getBoundingClientRect();
      const mx = (e.clientX - r.left) / r.width; const my = (e.clientY - r.top) / r.height;
      setView((cur) => {
        const c = cur ?? fit;
        const w = Math.min(Math.max(c.w * (e.deltaY < 0 ? 1 / 1.15 : 1.15), 120), W);
        const h = (w * H) / W; const ch = (c.w * H) / W;
        return {
          w,
          x: Math.min(Math.max(c.x + mx * (c.w - w), 0), W - w),
          y: Math.min(Math.max(c.y + my * (ch - h), 0), H - h),
        };
      });
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, [fit, W, H]);

  const drag = useRef<{ sx: number; sy: number; v: View } | null>(null);
  const onDown = (e: React.PointerEvent) => {
    (e.currentTarget as Element).setPointerCapture(e.pointerId);
    drag.current = { sx: e.clientX, sy: e.clientY, v };
  };
  const onMove = (e: React.PointerEvent) => {
    const d = drag.current;
    if (!d) return;
    const k = d.v.w / width;
    setView({
      w: d.v.w,
      x: Math.min(Math.max(d.v.x - (e.clientX - d.sx) * k, 0), W - d.v.w),
      y: Math.min(Math.max(d.v.y - (e.clientY - d.sy) * k, 0), H - (d.v.w * H) / W),
    });
  };

  // ---- derived state -------------------------------------------------------
  const states = timelines.map((tl) => stateAt(tl, clock, failures[tl.route.vehicleId]));
  const [hover, setHover] = useState<{ ri: number; si: number } | null>(null);
  const px = (n: number) => n * u;
  const dim = (id: string) => (selectedVehicleId && selectedVehicleId !== id ? 0.25 : 1);
  const toScreen = (x: number, y: number) => ({ left: ((x - v.x) / v.w) * width, top: ((y - v.y) / vh) * (width * H / W) });

  const setHoverStop = (h: { ri: number; si: number } | null, key: string | null) => {
    setHover(h);
    onHoverStop?.(key);
  };

  return (
    <div className="p12-map-layout">
      <div ref={wrapRef} className="p12-map-viewport">
        <svg
          ref={svgRef}
          viewBox={`${v.x} ${v.y} ${v.w} ${vh}`}
          className="p12-city-map"
          style={{ aspectRatio: `${W} / ${H}`, cursor: drag.current ? 'grabbing' : 'grab' }}
          onPointerDown={onDown}
          onPointerMove={onMove}
          onPointerUp={() => { drag.current = null; }}
          onPointerLeave={() => { drag.current = null; }}
          role="img"
          aria-label="Schematic map of vehicle routes at the simulation clock"
        >
          <rect x={0} y={0} width={W} height={H} fill="#252B54" />
          <polyline points={pts(city.river)} fill="none" stroke="#279B91" strokeWidth={30} strokeLinejoin="round" opacity={0.65} />

          {/* roads: casing first, fill on top */}
          {city.edges.map((e) => (
            <polyline key={`c${e.id}`} points={pts(e.pts)} fill="none" stroke={ROAD_CASING[e.kind]}
              strokeWidth={ROAD_PX[e.kind] + 2} strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
          ))}
          {city.edges.map((e) => (
            <polyline key={`f${e.id}`} points={pts(e.pts)} fill="none" stroke={ROAD_FILL[e.kind]}
              strokeWidth={ROAD_PX[e.kind]} strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
          ))}

          {/* closures */}
          {closurePaths.map(({ c, path }, i) => (
            <g key={`cl${i}`}>
              <polyline points={pts(path.pts)} fill="none" stroke={DIFF_COLOR.broken} strokeWidth={6}
                strokeLinecap="round" strokeLinejoin="round" opacity={0.85} vectorEffect="non-scaling-stroke" />
              <polyline points={pts(path.pts)} fill="none" stroke="#FFF7EB" strokeWidth={2} strokeDasharray="6 6"
                vectorEffect="non-scaling-stroke" />
              <text x={path.pts[Math.floor(path.pts.length / 2)][0]} y={path.pts[Math.floor(path.pts.length / 2)][1] - px(10)}
                fontSize={px(11)} fontWeight={600} textAnchor="middle" fill={DIFF_COLOR.broken}
                stroke="#252B54" strokeWidth={px(3)} paintOrder="stroke">{c.label ?? 'Closed'}</text>
            </g>
          ))}

          {/* ghosts: previous plan */}
          {ghosts.map((g) => (
            <polyline key={`g${g.route.vehicleId}`} points={pts(g.fullPath)} fill="none" stroke="#7A8794" strokeWidth={3}
              strokeDasharray="7 6" strokeLinecap="round" strokeLinejoin="round" opacity={0.55 * dim(g.route.vehicleId)}
              vectorEffect="non-scaling-stroke" />
          ))}

          {/* current plan: full route faint, driven part solid */}
          {timelines.map((tl, ri) => {
            const id = tl.route.vehicleId; const col = colorOf(id);
            return (
              <g key={`r${id}`} opacity={dim(id)}>
                <polyline points={pts(tl.fullPath)} fill="none" stroke={col} strokeWidth={5} opacity={0.28}
                  strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
                <polyline points={pts(states[ri].traveled)} fill="none" stroke={col} strokeWidth={5}
                  strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
              </g>
            );
          })}

          {/* unplaced deliveries */}
          {unplacedLocationIds.map((id) => {
            const l = graph.location(id);
            return (
              <g key={`u${id}`}>
                <circle cx={l.x} cy={l.y} r={px(9)} fill="#fff" stroke={DIFF_COLOR.broken} strokeWidth={px(2.5)} />
                <path d={`M${l.x - px(4)} ${l.y - px(4)}L${l.x + px(4)} ${l.y + px(4)}M${l.x + px(4)} ${l.y - px(4)}L${l.x - px(4)} ${l.y + px(4)}`}
                  stroke={DIFF_COLOR.broken} strokeWidth={px(2)} strokeLinecap="round" />
              </g>
            );
          })}

          {/* depot */}
          {city.locations.filter((l) => l.isDepot).map((l) => (
            <g key={`d${l.id}`}>
              <rect x={l.x - px(9)} y={l.y - px(9)} width={px(18)} height={px(18)} rx={px(3)} fill="#F07879" stroke="#FFF7EB" strokeWidth={px(2)} />
              <text x={l.x} y={l.y + px(3.5)} fontSize={px(10)} fontWeight={700} textAnchor="middle" fill="#191F45">D</text>
              <text x={l.x + px(13)} y={l.y + px(4)} fontSize={px(11)} fill="#FFF7EB" stroke="#252B54" strokeWidth={px(3)} paintOrder="stroke">{l.name}</text>
            </g>
          ))}

          {/* stops */}
          {timelines.map((tl, ri) => {
            const id = tl.route.vehicleId; const col = colorOf(id);
            return (
              <g key={`s${id}`} opacity={dim(id)}>
                {tl.route.stops.map((s, si) => {
                  const l = graph.location(s.locationId);
                  const done = clock >= s.depart;
                  const diff = stopStatus[s.key];
                  const ring = diff ? DIFF_COLOR[diff] : col;
                  const hot = highlightedKey === s.key || (hover?.ri === ri && hover.si === si);
                  const r = px(hot ? 11.5 : 9.5);
                  return (
                    <g key={`${s.key}-${si}`} style={{ cursor: 'pointer' }}
                      onPointerDown={(e) => e.stopPropagation()}
                      onPointerEnter={() => setHoverStop({ ri, si }, s.key)}
                      onPointerLeave={() => setHoverStop(null, null)}>
                      {hot && <circle cx={l.x} cy={l.y} r={r + px(5)} fill={ring} opacity={0.25} />}
                      {s.kind === 'pickup'
                        ? <rect x={l.x - r * 0.85} y={l.y - r * 0.85} width={r * 1.7} height={r * 1.7} rx={px(2)}
                            transform={`rotate(45 ${l.x} ${l.y})`} fill={done ? col : '#fff'} stroke={ring} strokeWidth={px(2.5)} />
                        : <circle cx={l.x} cy={l.y} r={r} fill={done ? col : '#fff'} stroke={ring} strokeWidth={px(2.5)} />}
                      <text x={l.x} y={l.y + px(3.5)} fontSize={px(10)} fontWeight={700} textAnchor="middle"
                        fill={done ? '#fff' : col} style={{ pointerEvents: 'none' }}>{si + 1}</text>
                      {newKeys.includes(s.key) && (
                        <text x={l.x} y={l.y - r - px(5)} fontSize={px(9)} fontWeight={700} textAnchor="middle" fill="#FFF7EB"
                          stroke="#252B54" strokeWidth={px(3)} paintOrder="stroke">NEW</text>
                      )}
                      {(hot || selectedVehicleId === id) && (
                        <text x={l.x + r + px(4)} y={l.y + px(4)} fontSize={px(11)} fill="#FFF7EB" stroke="#252B54"
                          strokeWidth={px(3)} paintOrder="stroke" style={{ pointerEvents: 'none' }}>{graph.name(s.locationId)}</text>
                      )}
                    </g>
                  );
                })}
              </g>
            );
          })}

          {/* vehicles */}
          {timelines.map((tl, ri) => {
            const id = tl.route.vehicleId; const st = states[ri]; const col = colorOf(id);
            const [x, y] = st.pos; const failed = st.status === 'failed';
            return (
              <g key={`v${id}`} opacity={dim(id)} style={{ cursor: 'pointer' }}
                onPointerDown={(e) => e.stopPropagation()}
                onClick={() => onSelectVehicle?.(selectedVehicleId === id ? null : id)}>
                {st.status === 'servicing' && <circle cx={x} cy={y} r={px(19)} fill={col} opacity={0.22} />}
                {st.status === 'waiting' && <circle cx={x} cy={y} r={px(18)} fill="none" stroke={col} strokeWidth={px(2)} strokeDasharray={`${px(3)} ${px(3)}`} />}
                {selectedVehicleId === id && <circle cx={x} cy={y} r={px(21)} fill="none" stroke="#111827" strokeWidth={px(1.5)} />}
                <circle cx={x} cy={y} r={px(13)} fill={failed ? '#B83F50' : col} stroke="#FFF7EB" strokeWidth={px(2.5)} />
                <text x={x} y={y + px(3.5)} fontSize={px(10)} fontWeight={700} textAnchor="middle" fill="#fff" style={{ pointerEvents: 'none' }}>
                  {id.replace(/^vehicle[-_ ]?/i, '').slice(0, 3)}
                </text>
                {failed && (
                  <path d={`M${x - px(8)} ${y - px(8)}L${x + px(8)} ${y + px(8)}M${x + px(8)} ${y - px(8)}L${x - px(8)} ${y + px(8)}`}
                    stroke={DIFF_COLOR.broken} strokeWidth={px(3)} strokeLinecap="round" />
                )}
              </g>
            );
          })}
        </svg>

        {/* hover details */}
        {hover && timelines[hover.ri]?.route.stops[hover.si] && (() => {
          const tl = timelines[hover.ri]; const s = tl.route.stops[hover.si];
          const l = graph.location(s.locationId); const pos = toScreen(l.x, l.y);
          const wait = Math.max(0, s.start - s.arrival);
          return (
            <div role="tooltip" className="p12-map-tooltip" style={{
              left: Math.min(pos.left + 14, width - 230), top: Math.max(pos.top - 10, 4),
            }}>
              <div style={{ fontWeight: 600 }}>{graph.name(s.locationId)}</div>
              <div>{tl.route.vehicleId} · stop {hover.si + 1}{s.kind === 'pickup' ? ' (pickup)' : ''}</div>
              <div>Arrives {fmtTime(s.arrival)}{wait > 0 ? `, waits ${wait} min` : ''}</div>
              <div>Service {fmtTime(s.start)}–{fmtTime(s.depart)}</div>
              {s.windowOpen !== undefined && s.windowClose !== undefined && <div>Window {fmtTime(s.windowOpen)}–{fmtTime(s.windowClose)}</div>}
              <div>Load after: {s.loadAfter} / {tl.route.capacity}</div>
              {stopStatus[s.key] && <div style={{ color: DIFF_COLOR[stopStatus[s.key]], fontWeight: 600 }}>{stopStatus[s.key]}</div>}
            </div>
          );
        })()}

        <button type="button" className="p12-map-fit" onClick={() => setView(null)}>Fit to routes</button>
      </div>

      {/* vehicle status at the clock */}
      <div className="p12-vehicle-list">
        <div className="p12-vehicle-list-heading">Vehicles at <b>{fmtTime(clock)}</b></div>
        {timelines.map((tl, ri) => {
          const id = tl.route.vehicleId; const st = states[ri];
          const load = loadAt(tl.route, clock); const pct = tl.route.capacity ? Math.min(100, (load / tl.route.capacity) * 100) : 0;
          return (
            <button key={id} type="button" className={`p12-vehicle-card ${selectedVehicleId === id ? 'is-selected' : ''} ${st.status === 'failed' ? 'is-failed' : ''}`} onClick={() => onSelectVehicle?.(selectedVehicleId === id ? null : id)}>
              <div className="p12-vehicle-card-heading">
                <span style={{ width: 10, height: 10, borderRadius: 5, background: colorOf(id), flex: 'none' }} />
                <strong>{id}</strong>
                <span className="p12-vehicle-load">{load} / {tl.route.capacity}</span>
              </div>
              <div className="p12-vehicle-description">{describe(tl, st, graph, failures[id])}</div>
              <div className="p12-vehicle-progress" role="meter" aria-label={`${id} load`} aria-valuenow={load} aria-valuemin={0} aria-valuemax={tl.route.capacity}>
                <div style={{ width: `${pct}%`, background: pct >= 100 ? '#F07879' : colorOf(id) }} />
              </div>
            </button>
          );
        })}
        {Object.keys(stopStatus).length > 0 && (
          <div className="p12-map-diff-legend">
            {(Object.keys(DIFF_COLOR) as DiffClass[]).map((k) => (
              <span key={k} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                <span style={{ width: 10, height: 10, borderRadius: 5, border: `2.5px solid ${DIFF_COLOR[k]}`, boxSizing: 'border-box' }} />
                {k[0].toUpperCase() + k.slice(1)}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
