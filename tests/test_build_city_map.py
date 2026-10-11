import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_city_map as bcm  # noqa: E402


def make_locs(n=26, seed=3, with_xy=True):
    rng = random.Random(seed)
    locs = []
    for i in range(n):
        locs.append(
            {
                "id": "depot" if i == 0 else f"L{i}",
                "name": "Depot" if i == 0 else f"Place {i}",
                "x": rng.uniform(0, 100) if with_xy else None,
                "y": rng.uniform(0, 70) if with_xy else None,
                "isDepot": i == 0,
            }
        )
    return locs


def matrix_for(locs):
    import math

    return [
        [math.ceil(math.hypot(a["x"] - b["x"], a["y"] - b["y"]) / 4) for b in locs] for a in locs
    ]


def test_deterministic():
    locs = make_locs()
    assert bcm.build_city_map(locs, None, seed=5) == bcm.build_city_map(make_locs(), None, seed=5)


def test_all_locations_reachable_and_inside_canvas():
    for seed in range(8):
        city = bcm.build_city_map(make_locs(seed=seed), None, seed=seed)  # validate() raises if not
        for location in city["locations"]:
            assert 0 <= location["x"] <= bcm.W and 0 <= location["y"] <= bcm.H


def test_has_bridge_and_river():
    city = bcm.build_city_map(make_locs(), None, seed=7)
    assert any(e["kind"] == "bridge" for e in city["edges"])
    assert len(city["river"]) > 5


def test_mds_layout_from_matrix_only():
    xy = make_locs()
    matrix = matrix_for(xy)
    blank = [{**location, "x": None, "y": None} for location in xy]
    city = bcm.build_city_map(blank, matrix, seed=7)
    assert len(city["locations"]) == len(xy)


def test_stops_keep_clear_of_each_other():
    city = bcm.build_city_map(make_locs(40, seed=9), None, seed=9)
    locs = city["locations"]
    for i in range(len(locs)):
        for j in range(i + 1, len(locs)):
            d = ((locs[i]["x"] - locs[j]["x"]) ** 2 + (locs[i]["y"] - locs[j]["y"]) ** 2) ** 0.5
            assert d > 10
