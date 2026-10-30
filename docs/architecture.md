# Architecture, version 0.3

## Runtime boundaries

```text
humanity/engine/       Python dataclasses, seeded randomness, decisions, perception,
                      actions, ordered systems, events, and snapshot validation
humanity/application.py
                      Serialized commands, complete saves, read-only projections
humanity/desktop/     PySide6 window, WebChannel bridge, worker, and static assets
humanity/data/        One shared JSON catalog for creation-time data and labels
src/ui/               HTML rendering, canvas drawing, formatting, and styles
src/main.js           View composition and user commands; no simulation clock
src/services/         Qt client and separate standalone browser adapter
src/core/, systems/   Original JavaScript engine, retained for the browser demo
```

The engine never imports Qt. It uses readable dataclasses and snake_case names; the serializer preserves the established camelCase JSON format. The desktop can run from a source checkout or a wheel containing the interface assets. Node.js is not a desktop runtime dependency.

## State ownership and threading

A single `SimulationWorker` QObject is moved to a QThread. Its controller, simulation, and single-shot QTimer are constructed in that thread. Commands are queued into it with Qt signals. A timer advances a tick and schedules the next tick after the result has been produced, so slow worlds do not build an unbounded backlog of timer requests. Speed choices express a target delay, not a guaranteed processing rate.

The GUI thread owns the window, WebChannel bridge, and native file dialogs. No background worker accesses a widget. A worker thread avoids blocking the Qt UI event loop; it is not a claim of CPU-parallel Python execution. If larger worlds require multiple CPU cores, the GUI-independent engine can later run in a separate process.

Frontend code sends commands and receives JSON projections. It does not own a desktop timer or mutate simulation state. Missing Qt transport in desktop mode produces an explicit error; it never silently starts the browser engine. The original standalone browser uses its own compatibility adapter, which is clearly separate from the Python runtime.

## Events and individual interpretation

Events record external facts. Individual appraisals become memories linked by event ID. Private self-experiences are appraised only by their owner; local events reach participants and at most four nearby observers. The controlled public achievement announcement reaches up to twelve sampled bystanders plus participants.

Directed relationships belong to the observer. Internal emotions and public presentation are separate. The last independent utility decision can differ from a subsequent outward social reaction.

`emotion.py` owns the five response equations and time decay. `perception.py` owns appraisal, coping and learning. Material action outcomes emit events rather than changing emotion directly. Appraisal memories include dimensions, before/after emotion state and reaction reasons. Direct replies are deferred events with a cause ID; response events cannot emit further replies.

## Adding a Python system

A system has a unique identifier, phase, order, and synchronous update function. Phases run in this order:

```text
before → act → observe → after
```

```python
from humanity import Simulation
from humanity.engine.systems import System


def update_shared_project(context):
    state = context.world.extensions.setdefault("shared_project", {"progress": 0})
    state["progress"] += context.random() * 0.01


project = System("shared-project", "after", update_shared_project, order=20)
simulation = Simulation(systems=[project])
simulation.step(24)
restored = Simulation.from_snapshot(simulation.snapshot(), systems=[project])
```

Within a phase, systems sort by numeric order then ID. Use `context.random()`, `context.emit(**event_fields)`, and `context.act(agent, decision)`. Store serializable module data in `world.extensions` or `agent.extensions`; arbitrary namespace keys are preserved by serialization. Events emitted after observation remain queued until the next tick, including after save/restore.

Actions are registered through `actions={"action-id": handler}`. A handler receives `ActionContext` and returns `ActionResult`. Default utility choices are in `engine/decision.py`; adding a new default option currently requires a focused edit there. A generalized policy registry can be extracted when multiple features actually need it.

## Transport, projections, and files

Qt WebChannel exposes one narrow request slot and response/update signals. The bridge validates method names. Save/Load uses fixed application-data paths. Export/Open invokes native file choosers on the GUI thread; arbitrary JavaScript-supplied filesystem paths are not accepted.

A read-only loopback server on a random local port serves only interface assets. It has no HTTP simulation API. Python source, Git metadata, saves, hidden files, and paths outside the asset root are not served. Main-frame navigation is restricted to the application origin. The Qt-supplied WebChannel library is injected at document creation.

View projections include Python-computed metrics and complete memories for the selected person. Other people's memory lists are trimmed to recent context and the current experiment to reduce transport cost. Total memory counts remain accurate. Selecting another person requests a fresh projection. Projections never replace engine state and are explicitly rejected as snapshots.

Complete saves use version-2 world JSON and the seeded random stream. Version-1 data has an explicit, one-way migration; the original automatic session is backed up and old metric history is cleared. New saves are rejected by the legacy browser model. They are written to a temporary sibling file, flushed, and atomically replaced. A manual checkpoint (`world.json`) is independent of the automatic closing session (`session.json`). Resume starts paused. An unreadable session is renamed to a recoverable backup before a replacement is written. User-selected legacy JSON files provide migration into the desktop; browser localStorage is not shared with Qt.

## Compatibility and scaling

Both engines use the same catalog and 32-bit Mulberry32 generator, including the original UTF-16 seed-hashing behavior. Migration tests verify preservation of identity, traits and memories, and deterministic continuation under the new Python rules. The engines intentionally differ in model semantics; exact behavioral equivalence is no longer expected. Optional null fields may be omitted in Python's compact JSON; their meaning is unchanged. Incompatible future schemas need explicit migrations, not silent reinterpretation.

The API ceiling remains 300 people and the interface offers up to 240. Some selection and relationship scans are quadratic; this is a bounded prototype rather than an unlimited-population engine. Histories and memories are bounded. Profile before adding indexes, multiprocessing, or a database.

## Validation

- Python engine, persistence, projection, and extension tests use `unittest`.
- Migration tests invoke the original Node engine as an independent version-1 data source.
- Qt signal integration tests exercise the actual bridge, worker-owned timer, native chooser routing, and file saves without desktop automation.
- Asset-server tests check MIME types and that code/Git files are inaccessible.
- Existing Node behavioral tests and the static build keep the standalone browser compatible.

The Python engine has no AI-provider dependency. Personality labels and model weights remain exploratory assumptions; the five-emotion algorithms are theory-inspired hypotheses, not empirically validated psychology. See `model.md` for equations and paired experiments.
