import { describe, expect, it } from "vitest";
import { CityGraph, type CityMap } from "./cityGraph";
import { buildTimeline, loadAt, stateAt, type MapRoute } from "./timeline";

const city: CityMap = {
  version: 1,
  seed: 7,
  viewBox: [100, 70],
  nodes: [
    { id: "a", x: 10, y: 35 },
    { id: "b", x: 50, y: 35 },
    { id: "c", x: 90, y: 35 },
  ],
  edges: [
    { id: "ab", a: "a", b: "b", kind: "arterial", pts: [[10, 35], [50, 35]] },
    { id: "bc", a: "b", b: "c", kind: "local", pts: [[50, 35], [90, 35]] },
  ],
  river: [[0, 20], [100, 20]],
  locations: [
    { id: "DEPOT", name: "Depot", x: 10, y: 35, isDepot: true, nodeId: "a" },
    { id: "STOP", name: "Stop", x: 50, y: 35, isDepot: false, nodeId: "b" },
    { id: "LAST", name: "Last", x: 90, y: 35, isDepot: false, nodeId: "c" },
  ],
};

const route: MapRoute = {
  vehicleId: "V01",
  capacity: 10,
  originLocationId: "DEPOT",
  originDepart: 480,
  initialLoad: 5,
  stops: [
    { key: "D001", locationId: "STOP", kind: "delivery", arrival: 490, start: 495, depart: 500, loadAfter: 3 },
    { key: "D002", locationId: "LAST", kind: "delivery", arrival: 510, start: 510, depart: 515, loadAfter: 1 },
  ],
};

describe("timeline", () => {
  const timeline = buildTimeline(route, new CityGraph(city));
  it("reports idle, driving, waiting, servicing and complete states", () => {
    expect(stateAt(timeline, 479).status).toBe("idle");
    expect(stateAt(timeline, 485).status).toBe("driving");
    expect(stateAt(timeline, 492).status).toBe("waiting");
    expect(stateAt(timeline, 497).status).toBe("servicing");
    expect(stateAt(timeline, 520).status).toBe("idle");
    expect(stateAt(timeline, 520, 515).status).toBe("failed");
  });
  it("holds position during a wait and changes load only after departure", () => {
    expect(stateAt(timeline, 492).pos).toEqual([50, 35]);
    expect(loadAt(route, 499)).toBe(5);
    expect(loadAt(route, 500)).toBe(3);
  });
});

describe("city graph", () => {
  it("returns deterministic symmetric paths and a single point for identical locations", () => {
    const graph = new CityGraph(city);
    expect(graph.path("DEPOT", "LAST")).toEqual(graph.path("DEPOT", "LAST"));
    expect(graph.path("DEPOT", "LAST").length).toBe(graph.path("LAST", "DEPOT").length);
    expect(graph.path("STOP", "STOP").pts).toEqual([[50, 35]]);
  });
});
