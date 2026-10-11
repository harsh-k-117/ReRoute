"""Freeze rules for completed and committed route work."""

from contract.models import Stop


def is_frozen(stop: Stop, now: int) -> bool:
    return stop.depart <= now or stop.arrival <= now <= stop.depart


def frozen_prefix(stops: list[Stop], now: int) -> list[Stop]:
    prefix: list[Stop] = []
    for stop in stops:
        if is_frozen(stop, now):
            prefix.append(stop.model_copy(update={"frozen": True}))
        else:
            break
    return prefix
