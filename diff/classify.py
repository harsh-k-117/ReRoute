"""Explainable delivery-level comparison between two plans."""

from contract.models import Classification, Diff, DiffRow, Plan


def _index(plan: Plan) -> dict[str, tuple[str, int]]:
    return {
        stop.delivery_id: (route.vehicle_id, stop.service_start)
        for route in plan.routes
        for stop in route.stops
        if stop.delivery_id
    }


def classify(previous: Plan, revised: Plan) -> Diff:
    before = _index(previous)
    after = _index(revised)
    all_ids = sorted(set(before) | set(after) | {item.delivery_id for item in revised.unplaced})
    rows: list[DiffRow] = []
    for delivery_id in all_ids:
        old = before.get(delivery_id)
        new = after.get(delivery_id)
        if new is None:
            classification = Classification.BROKEN
            cause = "no_feasible_slot"
            sentence = f"{delivery_id} could not be placed in the revised plan."
        elif old is None:
            classification = Classification.MOVED
            cause = "new_delivery"
            sentence = f"{delivery_id} was added to the revised plan."
        elif old[0] == new[0] and abs(old[1] - new[1]) <= 5:
            classification = Classification.KEPT
            cause = "unchanged"
            sentence = f"{delivery_id} remains on {new[0]} at a similar time."
        else:
            classification = Classification.MOVED
            cause = "replanned"
            sentence = f"{delivery_id} moved to {new[0]} or shifted because of the disruption."
        rows.append(
            DiffRow(
                delivery_id=delivery_id,
                classification=classification,
                cause_code=cause,
                sentence=sentence,
                before_vehicle_id=old[0] if old else None,
                after_vehicle_id=new[0] if new else None,
                before_eta=old[1] if old else None,
                after_eta=new[1] if new else None,
                badge="NEW" if old is None else None,
            )
        )
    return Diff(
        rows=rows,
        kept_count=sum(row.classification == Classification.KEPT for row in rows),
        moved_count=sum(row.classification == Classification.MOVED for row in rows),
        broken_count=sum(row.classification == Classification.BROKEN for row in rows),
    )
