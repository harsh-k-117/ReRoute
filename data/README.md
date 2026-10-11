# Data scenarios and importers

The checked-in JSON files in `data/scenarios/` are generated demo bundles. Do not
edit them by hand: change the generator or scenario-pack script, then run
`make scenarios` to regenerate all seven files deterministically.

All generated coordinates and travel times remain synthetic and authoritative
for planning. The frontend separately bundles an attributed OSM-derived Pune
road display dataset under `frontend/public/`; it is not used to calculate
travel times. The project does not fetch map, traffic, or GPS data at runtime.
The default city is Pune, with recognizable
place names and exact-match aliases for the text-input demo. Its featured closure
edge is the synthetic `Sangamwadi` ↔ `Bund Garden` connection
(`SANGAMWADI` ↔ `BUND_GARDEN`). Pune Municipal Corporation lists Sangam Bridge
and the Yerawada–Bund Garden bridge among city river crossings.

## Scenario catalogue

| File | Demonstrates | Suggested demo step |
|---|---|---|
| `baseline.json` | Feasible morning deliveries and three vehicle routes | Initial plan and stop timings |
| `closure.json` | Added travel time on the shared bridge edge | Road closure preview and revised ETAs |
| `failure.json` | Mid-route failure of the busiest vehicle | Freeze completed work and reassign remaining deliveries |
| `urgent.json` | Priority delivery released during the shift | Insert urgent work and show what moves |
| `cascade.json` | Closure followed by a vehicle failure | Replan again from the current plan |
| `stress.json` | 100 deliveries and 10 vehicles | Performance and scale demonstration; can be regenerated at 200/15 |
| `impossible.json` | One oversize order and one unreachable time window | Show explicit unplaced reasons |

Each bundle contains a contract-valid `scenario` object and a `disruptions` list.
The `data.importers.import_scenario_json` helper accepts either a plain scenario
object or one of these bundles. Disruptions remain next to the scenario so the
demo can load the event without changing the frozen contract models.

## Generators

```python
from data.generators import generate_city, generate_stress

city = generate_city(seed=7, n_deliveries=24, n_vehicles=5)
stress = generate_stress(seed=7, n_deliveries=200, n_vehicles=15)
```

`generate_city` adds two deliberately impossible deliveries by default. Pass
`include_impossible=False` for an all-feasible baseline. Both generators are
seeded and return validated `contract.models.Scenario` objects.

## Import formats

`import_scenario_json(source)` accepts a mapping, JSON text/bytes, a `Path`, or a
file path. It adapts explicit organizer aliases such as `orders`/`deliveries`,
`size`/`demand`, and `window_start`/`window_open`, then validates through the
Pydantic contract. Time windows may be integer minutes or `HH:MM` strings. It
does not fuzzy-match location names.

`import_scenario_csv(locations, vehicles, deliveries, travel_times, ...)` accepts
CSV text, bytes, paths, or open text files. The travel-time table can be an
ID-keyed square matrix or an edge list with `from,to,minutes`. Delivery and
vehicle references must match a location ID, name, or alias exactly. The
importer constructs and validates the same `Scenario` contract model.
