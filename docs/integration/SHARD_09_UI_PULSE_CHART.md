# SHARD 09 — UI Pulse Chart (Activity Viz)

Goal: show recent event volume as a sparkline/pulse.

Specs
- Canvas or SVG line chart (no heavy libs).
- Buckets: 5s or 10s windows; counts per event type.
- Gradient fill, glow on spike; dark/light aware.

Data
- Consume same event stream as observability page; maintain rolling buffer in client state.

Placement
- Dashboard header and observability page sidebar.
