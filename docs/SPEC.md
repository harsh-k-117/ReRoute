# S-01 — ReRoute: Dynamic Fleet & Delivery Replanning

**Domain:** 4 — Supply Chain & Optimization

## Problem Overview

Each morning, dispatchers decide which vehicle carries which deliveries and in what order. Vehicles have capacities, deliveries have sizes and time windows, and travel times vary. The plan rarely survives the day: a bridge closes, a vehicle breaks down, or an urgent delivery arrives. Dispatchers must then decide what to move and what to tell customers, often with a spreadsheet and experience. Changing the plan quickly is hard, and an unchecked change can overload a vehicle, miss a window, or undo a completed stop.

## The Challenge

Build a delivery-planning engine that assigns deliveries to vehicles while respecting capacity and time windows. Inputs include the depot, vehicles, deliveries, and a matrix of simulated travel times; no live mapping or GPS service may be used.

- Implement a routing or allocation algorithm that you can explain, and state its limits. Show arrival times at each stop, including any waiting before a window opens.
- Never overload a vehicle at any point on its route. A delivery that cannot be placed must be reported with the reason.
- Support three disruptions: a road closure that increases travel time between two locations for a stated period, a vehicle failure at a stated time, and an urgent delivery added during the day. Disruptions may be structured or described in text.
- Where a text report is interpreted, the dispatcher must confirm the resulting changes before they take effect. A report naming an unknown location must be rejected, not guessed at.
- Replanning starts from the current state: completed stops stay fixed, and a failed vehicle receives no stops after its failure time.
- Show the original and revised plans side by side, classifying every delivery as kept, moved, or broken, with a reason, so the dispatcher can explain changes to customers.
