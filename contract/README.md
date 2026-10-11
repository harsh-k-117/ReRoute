# Contract package

`models.py` is the source of truth for API, engine, NLP, replanning, and UI data shapes.
All times are integer minutes since midnight (D1), strict model validation rejects unknown
fields, and models are immutable after construction.

| Model | Purpose |
|---|---|
| `Location`, `Vehicle`, `Delivery`, `Scenario`, `ScenarioConfig` | Input data and time matrix |
| `Stop`, `Route`, `Plan`, `Unplaced`, `Reason` | Planned work and unplaced-delivery explanations |
| `RoadClosure`, `VehicleFailure`, `UrgentDelivery`, `Disruption` | Structured disruption inputs |
| `Proposal`, `SourceSpan` | Pending structured/text interpretation and source highlights |
| `Diff`, `DiffRow`, `Classification` | Kept/moved/broken comparison |
| `LedgerEntry`, `ReplanResult` | Replanning causes and result |
| `InvariantResult`, `ValidationReport`, `KpiSummary` | Validation and summary metrics |

`signatures.py` provides importable function stubs for all lanes. These stubs intentionally
raise `NotImplementedError`; they define interfaces, not implementations.

## Versioning

Before the team tags `contract-v1`, review the model shapes together and compare them with
`docs/SPEC.md` and any organizer-provided data. After the tag, changes are additive-only and
new fields must be optional with safe defaults. Record changes in `docs/CONTRACT_CHANGES.md`.

## OpenAPI

FastAPI generates OpenAPI from Pydantic request/response models. Once the API app is wired,
start it locally and use the repository's type-generation script (`make types`) to refresh
the TypeScript schema. Do not hand-edit generated types.

## Fixtures

`fixtures/scenario_micro.json` and `fixtures/plan_micro.json` are the small hand-checkable
example. Their intended arithmetic is documented in `fixtures/MICRO_WALKTHROUGH.md`.
