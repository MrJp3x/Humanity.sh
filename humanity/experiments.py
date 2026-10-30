"""Paired counterfactual checks with the same initial people in each condition.

These experiments characterize OUR model. They do not validate it against human
data. Each seed is one replicate; agents are not treated as independent samples.
"""

import argparse
from collections import Counter
from dataclasses import asdict
import json
from math import sqrt
from pathlib import Path
from statistics import mean, stdev

from . import __version__
from .engine.simulation import Simulation
from .engine.snapshots import atomic_write
from .engine.systems import metrics


CASES = {
    "secure": {"abundance": .9, "social_safety": .9, "pressure": .15},
    "unsafe": {"abundance": .9, "social_safety": .1, "pressure": .15},
    "scarce": {"abundance": .1, "social_safety": .9, "pressure": .15},
    "pressured": {"abundance": .9, "social_safety": .9, "pressure": .9},
}
MEASURES = ("wellbeing", "trust", "joy", "sadness", "fear", "anger", "disgust")


def run_experiment(seeds=12, population=24, steps=48):
    if type(seeds) is not int or not 2 <= seeds <= 1000:
        raise ValueError("Use 2–1000 replicate seeds")
    if type(steps) is not int or not 1 <= steps <= 1000:
        raise ValueError("Use 1–1000 hours")
    rows = []
    for index in range(seeds):
        original = Simulation(f"paired-{index}", population).snapshot()
        for name, conditions in CASES.items():
            sim = Simulation.from_snapshot(original)
            for key, value in conditions.items():
                sim.set_condition(key, value)
            choices = Counter()
            for _ in range(steps):
                sim.step()
                choices.update(a.last_decision.action_id for a in sim.world.agents)
            rows.append({"seed": f"paired-{index}", "case": name,
                         "metrics": asdict(metrics(sim.world)), "activities": dict(choices)})
    summary = {}
    for name in CASES:
        runs = [row for row in rows if row["case"] == name]
        summary[name] = {key: mean(row["metrics"][key] for row in runs) for key in MEASURES}
    paired = {}
    for name in CASES:
        if name == "secure":
            continue
        baseline = [r for r in rows if r["case"] == "secure"]
        changed = [r for r in rows if r["case"] == name]
        paired[name] = {}
        for key in MEASURES:
            differences = [b["metrics"][key] - a["metrics"][key] for a, b in zip(baseline, changed)]
            paired[name][key] = {"mean_difference": mean(differences),
                                 "standard_error_across_seeds": stdev(differences) / sqrt(seeds)}
    return {"model_version": __version__, "population": population, "hours": steps,
            "replicate_seeds": seeds, "conditions": CASES,
            "interpretation": "Model counterfactuals only; no empirical human validation. Standard errors describe seed variability, not uncertainty about the theory or coefficients.",
            "summary": summary, "paired_difference_from_secure": paired, "runs": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--population", type=int, default=24)
    parser.add_argument("--steps", type=int, default=48)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = run_experiment(args.seeds, args.population, args.steps)
        if args.output:
            atomic_write(args.output, json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({"summary": report["summary"], "replicate_seeds": args.seeds}, indent=2))
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
