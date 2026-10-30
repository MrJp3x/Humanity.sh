<div align="center">

# Humanity.sh

**A world of becoming.**

A Python society simulation with a PySide6 desktop window and an HTML observatory.

[فارسی](docs/README.fa.md) · [Architecture](docs/architecture.md) · [Model assumptions](docs/model.md) · [Contributing](CONTRIBUTING.md)

</div>

Each person has an identity, personality, values, beliefs, emotions, needs, memories, and directed relationships. People make decisions, interpret events differently, and change through experience. An observer can inspect individual lives and alter the conditions of their world.

## Desktop quick start

Requires **Python 3.11 or newer**. Node.js is not needed to run the desktop application.

```sh
git clone git@github.com:MrJp3x/Humanity.sh.git
cd Humanity.sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[desktop]"
python -m humanity.desktop
```

On Windows, activate with `.venv\Scripts\activate` instead. On macOS, after setup you can double-click `Humanity.command`. The interface is in Persian. HTML, JavaScript, fonts, and the Python engine run locally; no ChatGPT sign-in, network service, or AI API key is needed after installation.

Version 0.3 uses the same desktop runtime verified with PySide6 6.12.0. `requirements-desktop.txt` pins that tested top-level version; the desktop extra permits supported Qt 6 releases.

```sh
python -m humanity.desktop --fresh                    # Ignore the previous session
python -m humanity.desktop --data-dir ./my-worlds      # Choose a save directory
```

## Understand and extend the Python engine

Start with these files:

| File | Responsibility |
| --- | --- |
| `humanity/engine/models.py` | Dataclasses for people, personality, emotions, relationships, and worlds |
| `humanity/engine/emotion.py` | Five emotion algorithms, decay, recovery, and parameters |
| `humanity/engine/decision.py` | Explicit factors used to choose an action |
| `humanity/engine/perception.py` | Personal interpretations, internal feelings, and outward expression |
| `humanity/engine/actions.py` | Observable actions and their consequences |
| `humanity/engine/systems.py` | Needs, development, metrics, and the ordered system contract |
| `humanity/engine/simulation.py` | Clock, interventions, modules, and the public engine API |
| `humanity/application.py` | Application commands, persistence, and read-only interface projections |
| `humanity/desktop/` | PySide6 shell, Python worker, local assets, and WebChannel bridge |

The Python engine has **no Qt dependency**. Run experiments without opening a window:

```sh
python -m humanity.cli --seed hello-friend --population 48 --steps 240 --save world.json
python -m humanity.cli --load world.json --steps 24
```

```python
from humanity import Simulation

simulation = Simulation(seed="hello-friend", population=48)
simulation.step(24)
simulation.set_condition("pressure", 0.6)
simulation.announce_achievement("person-3")

person = simulation.world.agents[0]
print(person.identity.name, person.emotions.fear)
restored = Simulation.from_snapshot(simulation.snapshot())
```

The engine owns all state changes. HTML/CSS/JavaScript render the map and inspectors and send commands through Qt WebChannel. A single worker thread owns the Python world and clock. The frontend cannot run a second desktop simulation. See [the architecture and extension example](docs/architecture.md).

## The five-feeling model

**Conditions → personal appraisal → joy / sadness / fear / anger / disgust → coping → relationships and learning.**

Each reaction exposes the observed event, personal interpretation, emotional state before and after, and coping reason. The structure is inspired by appraisal research; coefficients are project hypotheses. It is **not empirically validated** and does not yet predict real human behavior. [Equations, sources, assumptions and known limitations](docs/model.md).

```sh
python -m humanity.experiments --seeds 12 --population 24 --steps 48 --output report.json
```

This compares identical starting people under four conditions across independent seeds. The report measures this model, not a real society.

## Observatory features

- A 2D society map, mood colors, relationships, and searchable residents.
- 24, 48, 120, or 240 people from the interface; 2–300 through the engine API.
- Separate personal history, beliefs, feelings, and public behavior.
- Directed trust: A's trust in B is independent of B's trust in A.
- Rest, conversation, help, creative work, reflection, and conflict resolution.
- Actual decision factors and individual memories linked to observed events.
- A controlled experiment: announce an achievement and compare five feelings, personal interpretation, before/after state, and outward response. Controlled help, rejection, insult and betrayal encounters use the same appraisal path.
- Pause, hourly steps, speed settings, and environmental interventions.
- Native JSON import/export plus separate manual saves and automatic session recovery.

New worlds begin after six actually simulated hours so there is already experience to inspect. A step represents an hour. The engine retains 400 recent events, 240 metric samples, and at most 82 memories per person, preserving the initial formative memory.

Desktop time continues while the window is in the background. Closing the application saves the session and stops the process. Reopening restores that session **paused**. Manual Save/Load uses a separate checkpoint for comparing futures. Files are stored in Qt's application-data directory unless `--data-dir` is supplied. Saves use atomic file replacement. An unreadable session is preserved as a backup rather than silently discarded.

### Existing web saves

Version 0.3 writes **version-2 snapshots**. Version-1 web/desktop files are migrated explicitly: anxiety becomes fear, comparison-related distress contributes to sadness, and disgust starts at zero. Existing memories and identities are preserved; incompatible metric history is cleared. The original automatic session is backed up before replacement. Migration changes future behavior. New saves cannot continue in the old browser engine. See [the complete mapping and limitations](docs/model.md). Browser local storage must still be exported manually.

## Tests and packaging

```sh
python -m unittest discover -s tests_python -v
```

The engine tests use the standard library. Qt integration tests require the desktop extra. Migration tests use Node.js 22+ as an oracle against the original implementation; Node is a **test dependency**, not a desktop runtime dependency.

```sh
python -m pip wheel . --no-deps --wheel-dir /tmp/humanity-wheels
```

The wheel includes the HTML interface and its assets. This is a Python desktop application, not yet a signed `.app`, `.dmg`, or Windows installer. Native installer automation is a separate future packaging step.

## Original standalone web demo

The old version-1 browser model remains as a legacy demo and migration reference. It does not include the desktop five-feeling model. It runs its own JavaScript engine without Python. It is separate from the desktop backend and should not be mistaken for a remote Python session.

```sh
npm run dev      # http://127.0.0.1:4173
npm run check
npm test
npm run build    # Static browser demo in dist/
```

The shared frontend selects the Qt bridge inside the desktop application and the browser adapter outside it. A missing desktop bridge produces a visible error rather than silently switching to JavaScript.

## Scope and license

This is an exploratory, rule-based model, not a validated predictor of people or societies. Numeric weights and synthetic backgrounds are explicit assumptions. Country systems, financial exchange, family structure, and general-purpose AI reasoning are not implemented yet. See [model assumptions](docs/model.md).

Code: [MIT](LICENSE), copyright © 2026 Pedram Asgari. The bundled [Vazirmatn](https://github.com/rastikerdar/vazirmatn) font uses [OFL 1.1](public/fonts/OFL.txt). Qt/PySide dependencies retain their own licenses.
