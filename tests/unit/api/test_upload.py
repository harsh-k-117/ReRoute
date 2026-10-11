from __future__ import annotations

import io
import json
import zipfile

from fastapi.testclient import TestClient

from api.main import app
from api.routes.upload import _safe_zip_extract
from data.importers.csv_importer import _clock


def test_scenario_json_preview_and_confirm_registers_upload() -> None:
    client = TestClient(app)
    payload = client.get("/templates/scenario_json").content

    preview = client.post(
        "/scenarios/upload/preview",
        files={"file": ("scenario.json", payload, "application/json")},
    )

    assert preview.status_code == 200
    body = preview.json()
    assert body["errors"] == []
    confirmed = client.post("/scenarios/upload/confirm", json={"token": body["token"]})
    assert confirmed.status_code == 200
    name = confirmed.json()["scenario_name"]
    assert any(item["name"] == name for item in client.get("/scenarios").json())


def test_csv_bundle_preview_accepts_bom_and_semicolon() -> None:
    client = TestClient(app)
    files = []
    for index, kind in enumerate(("locations_csv", "vehicles_csv", "deliveries_csv", "matrix_csv")):
        content = client.get(f"/templates/{kind}").content
        if index == 0:
            content = b"\xef\xbb\xbf" + content.replace(b",", b";")
        files.append(("file" if index == 0 else "files", (f"{kind}.csv", content, "text/csv")))
    response = client.post("/scenarios/upload/preview", files=files)
    assert response.status_code == 200
    assert response.json()["errors"] == []


def test_time_formats_and_zip_slip_are_rejected_or_normalized() -> None:
    assert _clock("9:05 am", "time") == 545
    assert _clock("9:05 pm", "time") == 1265
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../scenario.json", json.dumps({}))
    try:
        _safe_zip_extract(archive.getvalue())
    except ValueError as error:
        assert "zip-slip" in str(error)
    else:
        raise AssertionError("zip-slip entry was accepted")
