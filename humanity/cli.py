"""Run repeatable experiments without starting Qt or opening a window."""

import argparse
import json
from pathlib import Path

from .engine.simulation import Simulation
from .engine.snapshots import atomic_write, to_wire
from .engine.systems import metrics


def main():
    parser = argparse.ArgumentParser(description="Humanity.sh headless Python simulation")
    parser.add_argument("--seed", default="hello-friend")
    parser.add_argument("--population", type=int, default=48)
    parser.add_argument("--steps", type=int, default=24)
    parser.add_argument("--load", type=Path)
    parser.add_argument("--save", type=Path)
    args = parser.parse_args()
    if not 0 <= args.steps <= 1_000_000:
        parser.error("steps must be between 0 and 1000000")
    try:
        simulation = Simulation.from_snapshot(args.load.read_text(encoding="utf-8")) if args.load else Simulation(args.seed, args.population)
        remaining = args.steps
        while remaining:
            count = min(1000, remaining)
            simulation.step(count)
            remaining -= count
        if args.save:
            atomic_write(args.save, simulation.snapshot())
        print(json.dumps({"population": len(simulation.world.agents), **to_wire(metrics(simulation.world))}, ensure_ascii=False))
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
