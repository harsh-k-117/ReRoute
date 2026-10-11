// Turns a route's scheduled times into a position-over-time function.
// The plan's own arrival / start / depart values drive everything, so the map
// can never disagree with the Gantt chart.

import { appendPts, cumulative, pointAlong, upTo, type CityGraph, type Pt } from './cityGraph';

export type VehicleStatus = 'driving' | 'waiting' | 'servicing' | 'idle' | 'failed';

export interface MapStop {
  /** Stable key, usually the delivery id. Used for hover, diff status and highlighting. */
  key: string;
  locationId: string;
  kind: 'delivery' | 'pickup';
  arrival: number;   // minutes since midnight
  start: number;     // service start = max(arrival, window open)
  depart: number;    // start + service time
  loadAfter: number;
  windowOpen?: number;
  windowClose?: number;
}

export interface MapRoute {
  vehicleId: string;
  capacity: number;
  originLocationId: string;
  originDepart: number;
  initialLoad: number;
  stops: MapStop[];
}

interface Segment {
  kind: 'drive' | 'wait' | 'service';
  t0: number;
  t1: number;
  pts: Pt[];
  cum: number[];
  stopIdx: number; // stop this segment leads to / happens at
}

export interface Timeline {
  route: MapRoute;
  segments: Segment[];
  fullPath: Pt[];
  origin: Pt;
}

export interface VehicleState {
  status: VehicleStatus;
  pos: Pt;
  stopIdx: number;          // current or next stop, -1 if none
  until: number | null;     // end of the current segment
  traveled: Pt[];           // path driven so far
}

export function buildTimeline(route: MapRoute, graph: CityGraph): Timeline {
  const origin = graph.location(route.originLocationId);
  const segments: Segment[] = [];
  const fullPath: Pt[] = [[origin.x, origin.y]];
  let at = route.originLocationId;
  let t = route.originDepart;

  route.stops.forEach((stop, i) => {
    const leg = graph.path(at, stop.locationId);
    appendPts(fullPath, leg.pts);
    segments.push({ kind: 'drive', t0: t, t1: stop.arrival, pts: leg.pts, cum: cumulative(leg.pts), stopIdx: i });
    const here = graph.location(stop.locationId);
    const p: Pt[] = [[here.x, here.y]];
    segments.push({ kind: 'wait', t0: stop.arrival, t1: stop.start, pts: p, cum: [0], stopIdx: i });
    segments.push({ kind: 'service', t0: stop.start, t1: stop.depart, pts: p, cum: [0], stopIdx: i });
    at = stop.locationId;
    t = stop.depart;
  });

  return { route, segments, fullPath, origin: [origin.x, origin.y] };
}

export function stateAt(tl: Timeline, t: number, failedAt?: number): VehicleState {
  let pos: Pt = tl.origin;
  const traveled: Pt[] = [tl.origin];
  let result: VehicleState | null = null;

  if (tl.segments.length && t < tl.segments[0].t0) {
    result = { status: 'idle', pos, stopIdx: 0, until: tl.segments[0].t0, traveled };
  }

  if (!result) {
    for (const seg of tl.segments) {
      if (t >= seg.t1) {
        if (seg.kind === 'drive') appendPts(traveled, seg.pts);
        pos = seg.pts[seg.pts.length - 1];
        continue;
      }
      if (seg.kind === 'drive') {
        const frac = (t - seg.t0) / (seg.t1 - seg.t0);
        appendPts(traveled, upTo(seg.pts, seg.cum, frac));
        pos = pointAlong(seg.pts, seg.cum, frac);
        result = { status: 'driving', pos, stopIdx: seg.stopIdx, until: seg.t1, traveled };
      } else {
        pos = seg.pts[0];
        result = { status: seg.kind === 'wait' ? 'waiting' : 'servicing', pos, stopIdx: seg.stopIdx, until: seg.t1, traveled };
      }
      break;
    }
  }

  if (!result) result = { status: 'idle', pos, stopIdx: -1, until: null, traveled };
  if (failedAt !== undefined && t >= failedAt) result = { ...result, status: 'failed', until: null };
  return result;
}

/** Load on board at time t: the load after the last stop whose service has finished. */
export function loadAt(route: MapRoute, t: number): number {
  let load = route.initialLoad;
  for (const s of route.stops) {
    if (s.depart <= t) load = s.loadAfter; else break;
  }
  return load;
}

export function fmtTime(min: number): string {
  const m = Math.round(min);
  const h = Math.floor(m / 60) % 24;
  return `${String(h).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;
}
