// Display-only road graph for the schematic city map.
// Never used for timing: the travel-time matrix stays authoritative (D1, D4).

export type Pt = [number, number];

export interface CityNode { id: string; x: number; y: number; locationId?: string }
export interface CityEdge { id: string; a: string; b: string; kind: 'local' | 'arterial' | 'bridge'; pts: Pt[] }
export interface CityLocation { id: string; name: string; x: number; y: number; isDepot: boolean; nodeId: string }
export interface CityMap {
  version: number;
  seed: number;
  viewBox: [number, number];
  nodes: CityNode[];
  edges: CityEdge[];
  river: Pt[];
  locations: CityLocation[];
}

export interface RoutePath { edgeIds: string[]; pts: Pt[]; length: number }

// ---- polyline helpers -----------------------------------------------------
export function cumulative(pts: Pt[]): number[] {
  const c = [0];
  for (let i = 1; i < pts.length; i++) {
    c.push(c[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  }
  return c;
}

export function pointAlong(pts: Pt[], cum: number[], frac: number): Pt {
  const total = cum[cum.length - 1];
  if (pts.length === 1 || total === 0) return pts[0];
  const target = Math.min(Math.max(frac, 0), 1) * total;
  for (let i = 1; i < pts.length; i++) {
    if (target <= cum[i]) {
      const seg = cum[i] - cum[i - 1];
      const f = seg === 0 ? 0 : (target - cum[i - 1]) / seg;
      return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f];
    }
  }
  return pts[pts.length - 1];
}

/** Points from the start of the polyline up to `frac` of its length. */
export function upTo(pts: Pt[], cum: number[], frac: number): Pt[] {
  const total = cum[cum.length - 1];
  if (pts.length === 1 || total === 0) return [pts[0]];
  const target = Math.min(Math.max(frac, 0), 1) * total;
  const out: Pt[] = [pts[0]];
  for (let i = 1; i < pts.length; i++) {
    if (target >= cum[i]) {
      out.push(pts[i]);
    } else {
      out.push(pointAlong(pts, cum, frac));
      break;
    }
  }
  return out;
}

export function appendPts(target: Pt[], more: Pt[]): void {
  for (const p of more) {
    const last = target[target.length - 1];
    if (!last || last[0] !== p[0] || last[1] !== p[1]) target.push(p);
  }
}

// ---- graph ----------------------------------------------------------------
interface Arc { to: string; edge: CityEdge; forward: boolean; len: number }

export class CityGraph {
  readonly map: CityMap;
  private adj = new Map<string, Arc[]>();
  private locs = new Map<string, CityLocation>();
  private nodePos = new Map<string, Pt>();
  private cache = new Map<string, RoutePath>();

  constructor(map: CityMap) {
    this.map = map;
    for (const l of map.locations) this.locs.set(l.id, l);
    for (const n of map.nodes) this.nodePos.set(n.id, [n.x, n.y]);
    for (const e of map.edges) {
      const len = cumulative(e.pts).slice(-1)[0];
      this.push(e.a, { to: e.b, edge: e, forward: true, len });
      this.push(e.b, { to: e.a, edge: e, forward: false, len });
    }
  }

  private push(from: string, arc: Arc) {
    const list = this.adj.get(from);
    if (list) list.push(arc); else this.adj.set(from, [arc]);
  }

  location(id: string): CityLocation {
    const l = this.locs.get(id);
    if (!l) throw new Error(`map has no location "${id}"`);
    return l;
  }

  name(id: string): string {
    return this.locs.get(id)?.name ?? id;
  }

  /** Shortest road path between two locations, for drawing only. */
  path(fromLoc: string, toLoc: string): RoutePath {
    const key = `${fromLoc}|${toLoc}`;
    const hit = this.cache.get(key);
    if (hit) return hit;
    const result = this.compute(fromLoc, toLoc);
    this.cache.set(key, result);
    return result;
  }

  private compute(fromLoc: string, toLoc: string): RoutePath {
    const A = this.location(fromLoc);
    const B = this.location(toLoc);
    if (A.nodeId === B.nodeId) return { edgeIds: [], pts: [[A.x, A.y]], length: 0 };

    const dist = new Map<string, number>([[A.nodeId, 0]]);
    const prev = new Map<string, { node: string; arc: Arc }>();
    const done = new Set<string>();
    for (;;) {
      let u: string | null = null;
      let best = Infinity;
      for (const [n, d] of dist) {
        if (!done.has(n) && d < best) { best = d; u = n; }
      }
      if (u === null || u === B.nodeId) break;
      done.add(u);
      for (const arc of this.adj.get(u) ?? []) {
        const nd = best + arc.len;
        if (nd < (dist.get(arc.to) ?? Infinity)) {
          dist.set(arc.to, nd);
          prev.set(arc.to, { node: u, arc });
        }
      }
    }
    if (!prev.has(B.nodeId)) {
      // Unreachable on the display graph: fall back to a straight line.
      const pts: Pt[] = [[A.x, A.y], [B.x, B.y]];
      return { edgeIds: [], pts, length: cumulative(pts)[1] };
    }
    const steps: Arc[] = [];
    for (let n = B.nodeId; n !== A.nodeId;) {
      const p = prev.get(n)!;
      steps.push(p.arc);
      n = p.node;
    }
    steps.reverse();
    const pts: Pt[] = [[A.x, A.y]];
    const edgeIds: string[] = [];
    for (const s of steps) {
      edgeIds.push(s.edge.id);
      appendPts(pts, s.forward ? s.edge.pts : [...s.edge.pts].reverse());
    }
    return { edgeIds, pts, length: dist.get(B.nodeId) ?? 0 };
  }
}
