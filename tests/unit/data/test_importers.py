import json
from pathlib import Path

import pytest

from contract.models import Scenario
from data.importers import import_scenario_csv, import_scenario_json


def test_json_importer_accepts_plain_scenario_and_pack_shape():
    fixture = json.loads(Path("contract/fixtures/scenario_micro.json").read_text(encoding="utf-8"))
    expected = Scenario.model_validate(fixture)
    assert import_scenario_json(fixture) == expected
    assert import_scenario_json(json.dumps({"name": "micro-pack", "scenario": fixture})) == expected


def test_json_importer_maps_explicit_organizer_aliases_and_clock_strings():
    organizer_data = {
        "scenario_name": "sheet-export",
        "depot": "warehouse",
        "places": [
            {"id": "HOME", "name": "Depot", "aliases": ["warehouse"]},
            {"id": "SHOP", "name": "Shop", "aliases": ["market"]},
        ],
        "fleet": [
            {"vehicle_id": "V1", "name": "Van", "capacity": 5, "start_location": "warehouse"}
        ],
        "orders": [
            {
                "delivery_id": "D1",
                "destination_id": "market",
                "size": 2,
                "window_start": "09:00",
                "window_end": "10:00",
                "duration": 5,
            }
        ],
        "travel_time_matrix": [[0, 10], [10, 0]],
        "start_time": 480,
    }

    scenario = import_scenario_json(organizer_data)
    assert scenario.name == "sheet-export"
    assert scenario.depot_id == "HOME"
    assert scenario.deliveries[0].window_open == 540
    assert scenario.deliveries[0].location_id == "SHOP"


def test_json_importer_reports_invalid_contract_data_clearly():
    with pytest.raises(ValueError, match="does not match the ReRoute contract"):
        import_scenario_json({"name": "broken"})


def test_json_importer_rejects_unknown_location_without_guessing():
    organizer_data = {
        "name": "unknown-place",
        "depot_id": "HOME",
        "locations": [
            {"id": "HOME", "name": "Depot", "aliases": []},
            {"id": "SHOP", "name": "Shop", "aliases": []},
        ],
        "vehicles": [{"id": "V1", "name": "Van", "capacity": 4, "start_location_id": "HOME"}],
        "deliveries": [
            {
                "id": "D1",
                "location_id": "Shpo",
                "demand": 1,
                "window_open": 500,
                "window_close": 600,
                "service_time": 5,
            }
        ],
        "travel_times": [[0, 10], [10, 0]],
    }

    with pytest.raises(ValueError, match="unknown location 'Shpo'"):
        import_scenario_json(organizer_data)


def test_csv_importer_round_trips_matrix_and_resolves_exact_location_aliases():
    scenario = import_scenario_csv(
        "location_id,name,aliases\nHOME,Depot,warehouse\nSHOP,Shop,market\n",
        "vehicle_id,name,capacity,start_location\nV1,Van 1,5,warehouse\n",
        "delivery_id,location,demand,window_start,window_end,service_minutes\nD1,market,2,09:00,10:00,5\n",
        "from,to,minutes\nHOME,SHOP,10\n",
        name="csv-demo",
        depot_id="HOME",
        start_time="08:00",
    )

    assert scenario.name == "csv-demo"
    assert scenario.travel_times == [[0, 10], [10, 0]]
    assert scenario.vehicles[0].start_location_id == "HOME"
    assert scenario.deliveries[0].location_id == "SHOP"
    assert scenario.deliveries[0].window_open == 540


def test_csv_importer_rejects_unknown_location_without_guessing():
    with pytest.raises(ValueError, match="unknown location"):
        import_scenario_csv(
            "location_id,name\nHOME,Depot\nSHOP,Shop\n",
            "id,name,capacity,start_location_id\nV1,Van,5,HOME\n",
            "id,location_id,demand,window_open,window_close,service_time\nD1,Shpo,1,500,600,5\n",
            "from,to,minutes\nHOME,SHOP,10\n",
            depot_id="HOME",
        )
