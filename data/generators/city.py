"""Deterministic synthetic Pune scenario with a shared bridge edge."""

from __future__ import annotations

import math
import random

from contract.models import Delivery, Location, Scenario, ScenarioConfig, Vehicle

# Coordinates are synthetic relative positions, not a geographic or mapping feed.
# SANGAMWADI--BUND_GARDEN is the featured direct edge for the closure demo.
BRIDGE_EDGE = ("SANGAMWADI", "BUND_GARDEN")
_CITY_LOCATIONS: tuple[tuple[str, str, tuple[str, ...], float, float], ...] = (
    ("DEPOT", "Shivajinagar", ("Shivaji Nagar", "Shivajinagar Bus Stand"), 0.0, 0.0),
    ("DECCAN", "Deccan Gymkhana", ("Deccan",), 2.0, -1.0),
    ("CAMP", "Camp", ("Pune Camp",), 5.8, -2.1),
    ("SWARGATE", "Swargate", ("Swargate Bus Station",), 3.4, -5.8),
    ("KOTHRUD", "Kothrud", ("Kothrud Depot",), -5.1, -4.4),
    ("AUNDH", "Aundh", ("Aundh Gaon",), -5.4, 4.9),
    ("BANER", "Baner", ("Baner Road",), -9.3, 6.8),
    ("KOREGAON_PARK", "Koregaon Park", ("KP", "Koregaon Park Road"), 7.4, 1.7),
    ("YERAWADA", "Yerawada", ("Yerwada",), 9.1, 5.8),
    ("SANGAMWADI", "Sangamwadi", ("Sangamvadi", "Sangamwadi Bridge"), 6.6, 4.0),
    ("BUND_GARDEN", "Bund Garden", ("Bund Garden Road",), 8.1, 3.4),
    ("VIMAN_NAGAR", "Viman Nagar", ("Vimannagar",), 13.2, 7.2),
    ("HADAPSAR", "Hadapsar", ("Hadapsar Gaon",), 12.0, -6.1),
    ("KHARADI", "Kharadi", ("Kharadi Bypass",), 15.0, 0.8),
)
_SERVICE_CHOICES = (5, 10, 15)


def bridge_edge() -> tuple[str, str]:
    """Return the scenario location IDs forming the featured closure edge."""
    return BRIDGE_EDGE


def generate_city(
    seed: int,
    n_deliveries: int = 24,
    n_vehicles: int = 5,
    *,
    include_impossible: bool = True,
) -> Scenario:
    """Create a repeatable synthetic Pune delivery scenario.

    Travel times are ``ceil(Euclidean distance * 3.5)`` integer minutes. The
    matrix is symmetric and metric, and intentionally uses no live map or GPS
    data. When ``include_impossible`` is true, two final deliveries are
    deliberately infeasible: one exceeds every vehicle's capacity, while one
    has a close time earlier than the shortest depot trip.
    """
    if n_deliveries < 0:
        raise ValueError("n_deliveries must be non-negative")
    if n_vehicles <= 0:
        raise ValueError("n_vehicles must be positive")

    rng = random.Random(seed)
    locations = [
        Location(id=identifier, name=name, aliases=list(aliases), x=x, y=y)
        for identifier, name, aliases, x, y in _CITY_LOCATIONS
    ]
    index = {location.id: i for i, location in enumerate(locations)}
    travel_times = [
        [math.ceil(math.hypot(left.x - right.x, left.y - right.y) * 3.5) for right in locations]
        for left in locations
    ]
    capacities = [rng.randint(7, 11) for _ in range(n_vehicles)]
    vehicles = [
        Vehicle(
            id=f"V{vehicle_number:02d}",
            name=f"City van {vehicle_number:02d}",
            aliases=[f"Van {vehicle_number}", f"Vehicle {vehicle_number}"],
            capacity=capacity,
            shift_end=720,
            start_location_id="DEPOT",
        )
        for vehicle_number, capacity in enumerate(capacities, start=1)
    ]

    impossible_count = 2 if include_impossible and n_deliveries >= 2 else 0
    feasible_count = n_deliveries - impossible_count
    deliveries: list[Delivery] = []
    neighborhoods = [location.id for location in locations if location.id != "DEPOT"]
    bridge_ids = list(BRIDGE_EDGE)
    bridge_delivery_count = min(feasible_count, max(2, 2 * n_vehicles))
    for number in range(1, feasible_count + 1):
        if number <= bridge_delivery_count:
            # Balanced service windows on both ends make the shared bridge edge
            # appear in several natural route sequences.
            location_id = bridge_ids[(number - 1) % len(bridge_ids)]
            wave = (number - 1) // (2 * n_vehicles)
            window_open = 510 + wave * 25 + ((number - 1) // 2 % n_vehicles) * 8
        else:
            location_id = rng.choice(neighborhoods)
            window_open = 500 + rng.randint(0, 135)
        window_close = window_open + rng.choice((30, 40, 55, 70))
        deliveries.append(
            Delivery(
                id=f"D{number:03d}",
                location_id=location_id,
                demand=rng.randint(1, 3),
                window_open=window_open,
                window_close=window_close,
                service_time=rng.choice(_SERVICE_CHOICES),
            )
        )

    next_number = feasible_count + 1
    if include_impossible:
        max_capacity = max(capacities)
        deliveries.append(
            Delivery(
                id=f"D{next_number:03d}",
                location_id="DECCAN",
                demand=max_capacity + 1,
                window_open=500,
                window_close=620,
                service_time=10,
            )
        )
        next_number += 1
        farthest = max(
            (location for location in locations if location.id != "DEPOT"),
            key=lambda location: travel_times[index["DEPOT"]][index[location.id]],
        )
        shortest_arrival = min(
            travel_times[index[vehicle.start_location_id]][index[farthest.id]]
            for vehicle in vehicles
        )
        deliveries.append(
            Delivery(
                id=f"D{next_number:03d}",
                location_id=farthest.id,
                demand=1,
                window_open=481,
                window_close=480 + shortest_arrival - 1,
                service_time=5,
            )
        )

    return Scenario(
        name="pune-city",
        depot_id="DEPOT",
        locations=locations,
        vehicles=vehicles,
        deliveries=deliveries,
        travel_times=travel_times,
        now=480,
        start_time=480,
        config=ScenarioConfig(transfer_minutes=10),
        seed=seed,
    )


__all__ = ["BRIDGE_EDGE", "bridge_edge", "generate_city"]
