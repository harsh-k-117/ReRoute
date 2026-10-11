# Architecture

```text
scenario + contract
        |
        v
engine (travel -> construct -> simulate -> diagnose)
        |
        v
replan (freeze -> disruption handling -> revised plan)
        |
        +--> verify (independent invariant gate)
        +--> diff (kept / moved / broken reasons)
        |
        v
api (structured and confirmed text flows) -> frontend
```

The independent validator in `verify/` must never import `engine/`. Runtime mapping and GPS services are not used.