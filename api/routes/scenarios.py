from fastapi import APIRouter, HTTPException

from api.store import available_scenarios, load_scenario

router = APIRouter()


@router.get("/scenarios")
def list_scenarios() -> list[dict[str, object]]:
    return [
        {"name": scenario.name, "uploaded": scenario.name.startswith("uploaded-")}
        for scenario in available_scenarios()
    ]


@router.get("/scenarios/{name}")
def get_scenario(name: str) -> object:
    try:
        return load_scenario(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown scenario: {name}") from exc
