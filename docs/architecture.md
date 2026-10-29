# Architecture

## Boundaries

```text
src/core/       clock, ordered lifecycle, seeded randomness, events, snapshots
src/domain/     person creation, directed relationships, shared vocabulary
src/systems/    needs, utility decisions, action outcomes, perception, development
src/ui/         DOM rendering, map drawing, formatting; no simulation randomness
src/main.js     application controls, browser persistence, view composition
```

The engine can run in Node without a DOM. The UI calls the public engine API and reads world state. Rendering never consumes the engine's random stream. No framework, server state, or LLM provider is coupled to domain behavior.

## State ownership

`Simulation` owns a plain serializable `world`. People have stable string IDs. Directed relationship records are stored on the observer, keyed by the other person's ID. `agent.initialTraits` preserves creation-time personality while `agent.traits` can evolve.

External events record facts and their witnesses. A witness's appraisal becomes a personal memory referencing the event ID. An event is not a globally broadcast belief. Private actions are not delivered to bystanders; local events reach participants and at most four nearby observers. The controlled public achievement experiment reaches at most twelve sampled observers in addition to participants.

The public presentation of a person (`publicState`) is separate from their emotions. `lastDecision` is the latest independent utility choice; a later social reaction may change outward presentation without replacing that decision.

## Public engine API

```js
import { Simulation } from '../src/core/simulation.js';

const simulation = new Simulation({ seed: 'hello-friend', population: 48 });
simulation.step();                       // One simulated hour
simulation.step(24);
simulation.setCondition('pressure', .6);
simulation.announceAchievement('person-3');

const saved = simulation.snapshot();
const restored = Simulation.fromSnapshot(saved);
```

`setCondition` validates inputs and records the intervention. `announceAchievement` is an explicit observer intervention, marked `origin: 'observer'`, and is appraised immediately even while time is paused. It does not advance the clock. Users' intervention sequence is part of an experiment's input.

## Adding a system

Systems have a unique `id`, a `phase` (`before`, `act`, `observe`, `after`), numeric `order`, and synchronous `update(context)`. Within a phase, order is numeric then identifier. Duplicate IDs and invalid contracts are rejected.

```js
const sharedProject = {
  id: 'shared-project',
  phase: 'after',
  order: 20,
  update({ world, random, emit, act }) {
    const state = world.extensions.sharedProject ??= { progress: 0 };
    state.progress += random() * .01;
    // Keep this module's data inside its namespace.
    // Emit factual events when a milestone is actually reached.
  },
};

const simulation = new Simulation({ systems: [sharedProject] });
const restored = Simulation.fromSnapshot(simulation.snapshot(), {
  systems: [sharedProject],
});
```

`emit(event)` queues an event for the observation phase; events emitted after that phase are observed on the next step. Default action utilities live in `systems/decision.js`. Register an action through `actions: [[id, handler]]`; a custom `act` system can dispatch it via `act(agent, decision)`. Adding an option to the default utility policy currently requires a focused change to that policy. A policy-provider interface can be extracted when multiple modules need it; this version avoids an unused generalized framework.

Action handlers return `{ kind, text, visibility, publicText, warmth }` and receive `{ world, agent, target, decision }`. The shared dispatcher records the action outcome and memory. All stochastic simulation logic must use context randomness or the core random helpers, never `Math.random()` or real time. UI animation may use browser time because it cannot alter simulation state.

## Snapshots and compatibility

A snapshot contains a format marker, schema version, complete world state, random state, bounded histories, pending events, next IDs, and required system IDs. Restore validates the structure and ranges before constructing a replacement simulation. A snapshot that requires missing modules is rejected. Browser import leaves the current simulation intact on failure.

Version 1 has no migration layer because only one schema exists. When data contracts change incompatibly, add an explicit migration keyed by version and preserve fixtures for old snapshots. Module state should likewise carry a module version when it becomes persistent across releases.

## Scaling

The initial implementation targets dozens to a few hundred people. Candidate partners are sampled from known contacts; event witnesses are bounded. Some arrays are scanned per person, making parts of a tick quadratic in population. Recent history and memories are bounded. The interface offers up to 240 people; the API validates a ceiling of 300. This is not an architecture for unbounded populations. Measure before introducing indexes, a worker, or a database; the DOM-independent engine can move to a worker without changing the domain model.

## Validation

Node tests cover deterministic replay, restoring the random stream, divergent appraisals, internal/public divergence, history-sensitive interpretation, directed relationships, privacy, bounded states at 240 people, extension lifecycles, and invalid inputs. Browser verification covers the rendered controls and narrow/desktop layouts. CI repeats syntax/import checks, engine tests, and the static build.
