<div align="center">

# Humanity.sh

**A world of becoming.**

An extensible society simulation of individual minds, shared experiences, and evolving relationships.

[فارسی](docs/README.fa.md) · [Architecture](docs/architecture.md) · [Model assumptions](docs/model.md) · [Contributing](CONTRIBUTING.md)

</div>

Humanity.sh is an early social simulation with an observer's control panel. Every person starts with an identity, formative memories, personality traits, values, beliefs, needs, and emotions. People make decisions, experience outcomes, interpret what they observe, and develop relationships and beliefs over time.

The same news can mean something different to each observer. Someone can feel both happiness and envy while offering a warm public congratulations. Their interpretation is stored separately from the event itself and can influence later decisions.

## Run locally

Requires **Node.js 22 or newer**. There are no runtime or development package dependencies to install.

```sh
git clone git@github.com:MrJp3x/Humanity.sh.git
cd Humanity.sh
npm run dev
```

Open **http://127.0.0.1:4173**. The interface is in Persian and supports right-to-left layout and narrow screens.

```sh
npm run check   # Syntax, module imports, required assets
npm test        # Simulation invariants and behavioral scenarios
npm run build  # Static production output in dist/
node scripts/serve.mjs --dist
```

Any static host can serve `dist/`; no server-side runtime, API key, account, or external AI service is needed to run a world. The `.sh` in the project name is branding, not a shell-script implementation.

## First version

- A 2D society map, relationships, mood colors, and individual selection.
- 24, 48, 120, or 240 residents from the interface; 2–300 through the engine API.
- Separate identity, personality, values, beliefs, needs, emotions, and public behavior.
- Directed relationships: A's trust in B is independent of B's trust in A.
- Rest, conversation, help, creative work, reflection, and conflict resolution.
- Agent-specific appraisals of observed events, including simultaneous joy and envy.
- A decision inspector showing the actual utility factors used by the engine.
- Personal memories and a public event feed, with private actions excluded from observation.
- Pause, hourly steps, speed controls, and adjustable environmental conditions.
- A controlled experiment: publish an individual's achievement and compare observers' interpretations and outward responses.
- Manual browser saves plus validated JSON import/export, including the random generator's state.

New worlds begin after **six genuinely simulated hours** so there are already decisions and experiences to inspect. A step represents one hour. Worlds pause when the page is hidden and do not run after it closes. Saves are manual; unsaved progress is lost on reload. The engine retains 400 recent events, 240 metric samples, and at most 82 memories per person, preserving the initial formative memory.

## Extending the world

The engine is independent of the browser. Its ordered system lifecycle is:

```text
before → act → observe → after
needs    decisions / actions    subjective perception    development / metrics
```

Systems receive a context with world state, seeded randomness, event emission, and action dispatch. A module can keep its own serializable state in `world.extensions` or `agent.extensions`, register actions, and participate in a phase without changing the interface or the clock. See [the extension example](docs/architecture.md#adding-a-system).

There is deliberately no country, politics, or elaborate economic hierarchy in this version. Those are future modeling choices, rather than assumptions embedded in the core data model. Financial exchange is not implemented in v0.1.

## Scope and interpretation

This is an **exploratory, rule-based model**, not a reconstruction of a real human or a validated predictor of society. Numeric weights are explicit design assumptions. Personality labels and synthetic backgrounds do not establish scientific causal relationships. Memory truncation is a storage bound, not a psychological theory of forgetting.

Changing a rule can change an outcome. Use multiple seeds and explicit interventions when exploring a hypothesis. The current interface supports manually restoring a saved world to try another future; it does not yet automate batch experiments or statistical comparisons.

## License

Code: [MIT](LICENSE), copyright © 2026 Pedram Asgari.

Bundled [Vazirmatn](https://github.com/rastikerdar/vazirmatn) font: [SIL Open Font License 1.1](public/fonts/OFL.txt). Font licensing is independent of the code license.
