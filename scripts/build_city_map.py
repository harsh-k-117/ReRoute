#!/usr/bin/env python3
"""Build the static schematic city map used by the dispatcher map view.

Display geometry only: nothing here affects travel times. The matrix stays the
single source of truth for timing (D1, D4). Output is deterministic for a given
scenario + seed (D10) and needs no network.

Usage:
    python scripts/build_city_map.py --scenario data/scenarios/city.json \
        --out data/city_map.json [--seed 7] [--preview data/city_map.svg]

Scenario input (tolerant of field aliases):
    {"locations": [{"id": "...", "name": "...", "x": 12.3, "y": 45.6,
                    "is_depot": true}, ...],
     "matrix": [[0, 7, ...], ...]}          # minutes, same order as locations
x/y are optional. If any location lacks them, a layout is computed from the
matrix with classical MDS.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

W, H = 1000, 700  # viewBox of the schematic city
PAD = 90  # margin kept free around stops
STEP = 80  # grid spacing of road junctions
MIN_STOP_GAP = 30  # minimum distance between two stops
RIVER_CLEARANCE = 16  # minimum distance from a stop to the river


# --------------------------------------------------------------------------
# Input
# --------------------------------------------------------------------------
def load_scenario(path):
    raw = json.loads(Path(path).read_text())
    if isinstance(raw.get("scenario"), dict):
        raw = raw["scenario"]
    locs = raw.get("locations") or raw.get("nodes")
    if locs is None:
        raise SystemExit("scenario has no 'locations' list")
    if isinstance(locs, dict):
        locs = [{"id": k, **v} for k, v in locs.items()]
    out = []
    for loc in locs:
        out.append(
            {
                "id": str(loc["id"]),
                "name": str(loc.get("name", loc["id"])),
                "x": loc.get("x"),
                "y": loc.get("y"),
                "isDepot": bool(loc.get("is_depot") or loc.get("isDepot")),
            }
        )
    matrix = (
        raw.get("matrix")
        or raw.get("travel_times")
        or raw.get("travel_time_matrix")
        or raw.get("travelTimes")
    )
    if not any(location["isDepot"] for location in out):
        pick = next((location for location in out if location["id"].lower() == "depot"), out[0])
        pick["isDepot"] = True
    return out, matrix


# --------------------------------------------------------------------------
# Layout: x/y if supplied, else classical MDS on the time matrix
# --------------------------------------------------------------------------
def classical_mds(matrix):
    n = len(matrix)
    sym = [[(matrix[i][j] + matrix[j][i]) / 2.0 for j in range(n)] for i in range(n)]
    sq = [[v * v for v in row] for row in sym]
    row_mean = [sum(r) / n for r in sq]
    total_mean = sum(row_mean) / n
    b = [
        [-0.5 * (sq[i][j] - row_mean[i] - row_mean[j] + total_mean) for j in range(n)]
        for i in range(n)
    ]
    rng = random.Random(1)
    found = []
    for _ in range(2):
        v = [rng.random() - 0.5 for _ in range(n)]
        for _ in range(200):
            for u, _lam in found:
                dot = sum(p * q for p, q in zip(v, u, strict=True))
                v = [p - dot * q for p, q in zip(v, u, strict=True)]
            w = [sum(b[i][j] * v[j] for j in range(n)) for i in range(n)]
            norm = math.sqrt(sum(p * p for p in w)) or 1.0
            v = [p / norm for p in w]
        lam = sum(v[i] * sum(b[i][j] * v[j] for j in range(n)) for i in range(n))
        found.append((v, lam))
    coords = [[0.0, 0.0] for _ in range(n)]
    for k, (v, lam) in enumerate(found):
        scale = math.sqrt(lam) if lam > 0 else 1.0
        for i in range(n):
            coords[i][k] = v[i] * scale
    return coords


def fit_to_canvas(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    dx = (max(xs) - min(xs)) or 1.0
    dy = (max(ys) - min(ys)) or 1.0
    scale = min((W - 2 * PAD) / dx, (H - 2 * PAD) / dy)
    ox = (W - dx * scale) / 2 - min(xs) * scale
    oy = (H - dy * scale) / 2 - min(ys) * scale
    return [[p[0] * scale + ox, p[1] * scale + oy] for p in points]


def spread_apart(points, rng):
    """Nudge stops that sit almost on top of each other."""
    for _ in range(80):
        moved = False
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                dx = points[j][0] - points[i][0]
                dy = points[j][1] - points[i][1]
                d = math.hypot(dx, dy)
                if d >= MIN_STOP_GAP:
                    continue
                if d < 1e-6:
                    ang = rng.uniform(0, 2 * math.pi)
                    dx, dy, d = math.cos(ang), math.sin(ang), 1.0
                push = (MIN_STOP_GAP - d) / 2 + 0.5
                ux, uy = dx / d, dy / d
                points[i][0] -= ux * push
                points[i][1] -= uy * push
                points[j][0] += ux * push
                points[j][1] += uy * push
                moved = True
        for p in points:
            p[0] = min(max(p[0], 30), W - 30)
            p[1] = min(max(p[1], 30), H - 30)
        if not moved:
            break


def layout(locs, matrix, rng):
    if all(location["x"] is not None and location["y"] is not None for location in locs):
        raw = [[float(location["x"]), float(location["y"])] for location in locs]
    elif matrix:
        raw = classical_mds(matrix)
    else:
        raise SystemExit("need x/y on every location or a travel-time matrix")
    pts = fit_to_canvas(raw)
    spread_apart(pts, rng)
    return pts


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------
def poly_len(pts):
    return sum(
        math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts))
    )


def _ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])


def seg_cross(p1, p2, p3, p4):
    d1, d2 = _ccw(p3, p4, p1), _ccw(p3, p4, p2)
    d3, d4 = _ccw(p1, p2, p3), _ccw(p1, p2, p4)
    return (d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0)


def crosses(pts, river):
    for i in range(1, len(pts)):
        for j in range(1, len(river)):
            if seg_cross(pts[i - 1], pts[i], river[j - 1], river[j]):
                return True
    return False


def dist_to_polyline(p, pts):
    best = float("inf")
    for i in range(1, len(pts)):
        ax, ay = pts[i - 1]
        bx, by = pts[i]
        vx, vy = bx - ax, by - ay
        L = vx * vx + vy * vy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - ax) * vx + (p[1] - ay) * vy) / L))
        best = min(best, math.hypot(p[0] - (ax + t * vx), p[1] - (ay + t * vy)))
    return best


# --------------------------------------------------------------------------
# River: placed in the widest gap between stops so both banks have stops
# --------------------------------------------------------------------------
def make_river(points, rng):
    xs = sorted(p[0] for p in points)
    best_gap, cx = -1.0, xs[len(xs) // 2]
    for a, b in zip(xs, xs[1:], strict=False):
        mid = (a + b) / 2
        if W * 0.3 <= mid <= W * 0.7 and (b - a) > best_gap:
            best_gap, cx = b - a, mid
    amp = max(10.0, min(45.0, best_gap / 2 - 20)) if best_gap > 0 else 30.0
    phase = rng.uniform(0, math.pi)
    river = []
    y = -20
    while y <= H + 20:
        river.append([cx + amp * math.sin(y / H * 2 * math.pi * 1.1 + phase), float(y)])
        y += 20
    return river


def keep_stops_off_river(points, river):
    for p in points:
        for _ in range(20):
            if dist_to_polyline(p, river) >= RIVER_CLEARANCE:
                break
            near = min(river, key=lambda q: abs(q[1] - p[1]))
            p[0] += RIVER_CLEARANCE if p[0] >= near[0] else -RIVER_CLEARANCE


# --------------------------------------------------------------------------
# Road network
# --------------------------------------------------------------------------
class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        self.p[rb] = ra
        return True


def build_roads(locs, points, river, rng):
    cols = int((W - 60) / STEP) + 1
    rows = int((H - 60) / STEP) + 1
    arterial_rows = {1, 4, 7}
    arterial_cols = {1, 4, 7, 10}

    nodes = {}
    for r in range(rows):
        for c in range(cols):
            nid = f"j{r}_{c}"
            nodes[nid] = {
                "id": nid,
                "x": 30 + c * STEP + rng.uniform(-12, 12),
                "y": 30 + r * STEP + rng.uniform(-12, 12),
            }

    def make_edge(a, b, kind, curve=True):
        pa, pb = (nodes[a]["x"], nodes[a]["y"]), (nodes[b]["x"], nodes[b]["y"])
        pts = [list(pa)]
        if curve:
            mx, my = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
            dx, dy = pb[0] - pa[0], pb[1] - pa[1]
            d = math.hypot(dx, dy) or 1.0
            off = rng.uniform(-5, 5)
            pts.append([mx - dy / d * off, my + dx / d * off])
        pts.append(list(pb))
        return {"a": a, "b": b, "kind": kind, "pts": pts}

    candidates = []  # (edge, dropped_by_random)
    for r in range(rows):
        for c in range(cols):
            here = f"j{r}_{c}"
            if c + 1 < cols:
                art = r in arterial_rows
                e = make_edge(here, f"j{r}_{c + 1}", "arterial" if art else "local", curve=not art)
                candidates.append((e, (not art) and rng.random() < 0.10))
            if r + 1 < rows:
                art = c in arterial_cols
                e = make_edge(here, f"j{r + 1}_{c}", "arterial" if art else "local", curve=not art)
                candidates.append((e, (not art) and rng.random() < 0.10))
            if r + 1 < rows and c + 1 < cols and rng.random() < 0.06:
                candidates.append((make_edge(here, f"j{r + 1}_{c + 1}", "local"), False))

    for loc, p in zip(locs, points, strict=True):
        nodes[f"loc:{loc['id']}"] = {
            "id": f"loc:{loc['id']}",
            "x": p[0],
            "y": p[1],
            "locationId": loc["id"],
        }

    kept, repair, crossing = [], [], []
    for e, dropped in candidates:
        if crosses(e["pts"], river):
            crossing.append(e)
        elif dropped:
            repair.append(e)
        else:
            kept.append(e)

    # Spurs: each stop joins its two nearest same-bank junctions.
    junctions = [n for n in nodes.values() if "locationId" not in n]
    for loc, p in zip(locs, points, strict=True):
        lid = f"loc:{loc['id']}"
        ranked = sorted(junctions, key=lambda n: math.hypot(n["x"] - p[0], n["y"] - p[1]))
        joined = 0
        for j in ranked:
            spur = [list(p), [j["x"], j["y"]]]
            if crosses(spur, river):
                continue
            kept.append({"a": lid, "b": j["id"], "kind": "local", "pts": spur})
            joined += 1
            if joined == 2:
                break

    dsu = DSU()
    for n in nodes:
        dsu.find(n)
    for e in kept:
        dsu.union(e["a"], e["b"])

    def mid_y(e):
        return sum(p[1] for p in e["pts"]) / len(e["pts"])

    chosen = []
    if crossing:
        main = min(crossing, key=lambda e: abs(mid_y(e) - H / 2))
        chosen.append(main)
        target = mid_y(main) + (H / 3 if mid_y(main) < H / 2 else -H / 3)
        others = [e for e in crossing if abs(mid_y(e) - mid_y(main)) >= 2.5 * STEP]
        if others:
            chosen.append(min(others, key=lambda e: abs(mid_y(e) - target)))
    for e in chosen:
        e["kind"] = "bridge"
        kept.append(e)
        dsu.union(e["a"], e["b"])

    pool = [e for e in repair + crossing if e not in chosen]
    pool.sort(key=lambda e: poly_len(e["pts"]))
    for e in pool:
        if dsu.union(e["a"], e["b"]):
            if crosses(e["pts"], river):
                e["kind"] = "bridge"
            kept.append(e)

    edges = []
    for i, e in enumerate(kept):
        edges.append(
            {
                "id": f"e{i}",
                "a": e["a"],
                "b": e["b"],
                "kind": e["kind"],
                "pts": [[round(x, 1), round(y, 1)] for x, y in e["pts"]],
            }
        )

    used = {e["a"] for e in edges} | {e["b"] for e in edges}
    node_list = [
        {
            "id": n["id"],
            "x": round(n["x"], 1),
            "y": round(n["y"], 1),
            **({"locationId": n["locationId"]} if "locationId" in n else {}),
        }
        for n in nodes.values()
        if n["id"] in used
    ]
    return node_list, edges


# --------------------------------------------------------------------------
# Assemble, validate, preview
# --------------------------------------------------------------------------
def build_city_map(locs, matrix, seed=7):
    rng = random.Random(seed)
    points = layout(locs, matrix, rng)
    river = make_river(points, rng)
    keep_stops_off_river(points, river)
    nodes, edges = build_roads(locs, points, river, rng)
    city = {
        "version": 1,
        "seed": seed,
        "viewBox": [W, H],
        "nodes": nodes,
        "edges": edges,
        "river": [[round(x, 1), round(y, 1)] for x, y in river],
        "locations": [
            {
                "id": location["id"],
                "name": location["name"],
                "x": round(p[0], 1),
                "y": round(p[1], 1),
                "isDepot": location["isDepot"],
                "nodeId": f"loc:{location['id']}",
            }
            for location, p in zip(locs, points, strict=True)
        ],
    }
    validate(city)
    return city


def validate(city):
    adj = {}
    for e in city["edges"]:
        adj.setdefault(e["a"], []).append(e["b"])
        adj.setdefault(e["b"], []).append(e["a"])
    start = next(location["nodeId"] for location in city["locations"] if location["isDepot"])
    seen, stack = {start}, [start]
    while stack:
        for nb in adj.get(stack.pop(), []):
            if nb not in seen:
                seen.add(nb)
                stack.append(nb)
    missing = [location["id"] for location in city["locations"] if location["nodeId"] not in seen]
    if missing:
        raise SystemExit(f"locations unreachable from depot on the road graph: {missing}")


def write_preview(city, path):
    colors = {
        "local": ("#C9CFD6", 4, "#FFFFFF", 2),
        "arterial": ("#B4BCC6", 6, "#FFFFFF", 4),
        "bridge": ("#7C93AB", 8, "#F3F6F9", 5),
    }
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        f'<rect width="{W}" height="{H}" fill="#ECEFF1"/>',
        '<polyline fill="none" stroke="#BCD3E6" stroke-width="26" stroke-linejoin="round" '
        f'points="{" ".join(f"{x},{y}" for x, y in city["river"])}"/>',
    ]
    for layer in (0, 2):
        for e in city["edges"]:
            c = colors[e["kind"]]
            col, wid = (c[0], c[1]) if layer == 0 else (c[2], c[3])
            out.append(
                f'<polyline fill="none" stroke="{col}" stroke-width="{wid}" '
                f'stroke-linecap="round" stroke-linejoin="round" '
                f'points="{" ".join(f"{x},{y}" for x, y in e["pts"])}"/>'
            )
    for location in city["locations"]:
        shape = (
            f'<rect x="{location["x"] - 9}" y="{location["y"] - 9}" '
            'width="18" height="18" fill="#4B5563"/>'
            if location["isDepot"]
            else (
                f'<circle cx="{location["x"]}" cy="{location["y"]}" r="7" '
                'fill="#fff" stroke="#2F5DA8" stroke-width="2.5"/>'
            )
        )
        out.append(shape)
        out.append(
            f'<text x="{location["x"] + 11}" y="{location["y"] + 4}" '
            f'font-size="11" font-family="sans-serif" fill="#1F2937" '
            f'stroke="#fff" stroke-width="3" paint-order="stroke">{location["name"]}</text>'
        )
    out.append("</svg>")
    Path(path).write_text("\n".join(out))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--out", default="data/city_map.json")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--preview", help="optional SVG preview for eyeballing the layout")
    args = ap.parse_args(argv)

    locs, matrix = load_scenario(args.scenario)
    city = build_city_map(locs, matrix, args.seed)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(city, separators=(",", ":")))
    if args.preview:
        write_preview(city, args.preview)
    print(
        f"wrote {args.out}: {len(city['nodes'])} nodes, {len(city['edges'])} edges, "
        f"{len(city['locations'])} locations",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
