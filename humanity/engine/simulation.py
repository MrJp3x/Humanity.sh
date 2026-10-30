"""The public, GUI-independent Python engine."""

from math import isfinite

from .actions import builtin_actions, perform_action
from .agents import create_agent, relationship
from .events import emit
from .models import World
from .perception import observe_events
from .randomness import clamp, hash_seed, random, shuffle
from .snapshots import dumps, loads
from .systems import BUILTIN_SYSTEMS, PHASES, Context, System, metrics


class Simulation:
    def __init__(self, seed="hello-friend", population=48, *, systems=(), actions=None, world=None):
        if type(population) is not int or not 2 <= population <= 300:
            raise ValueError("Population must be between 2 and 300")
        if not isinstance(seed, str) or len(seed) >= 200:
            raise ValueError("Seed must be a string shorter than 200 characters")
        self.world = world if world is not None else World(seed=seed, rng=hash_seed(seed))
        self.systems: list[System] = []
        self.actions = builtin_actions()
        for action_id, handler in (actions or {}).items():
            self.register_action(action_id, handler)
        for system in (*BUILTIN_SYSTEMS, *systems):
            self.register_system(system)
        if world is None:
            self.world.agents = [create_agent(self.world, index) for index in range(population)]
            for agent in self.world.agents:
                acquaintances = shuffle(self.world, [a for a in self.world.agents if a.id != agent.id])[:4]
                for other in acquaintances:
                    relation = relationship(agent, other.id)
                    relation.trust = clamp(agent.beliefs.trust + (random(self.world) - .5) * .25)
                    relation.affection = .25 + random(self.world) * .5
                    relation.familiarity = .15 + random(self.world) * .35
            self.world.history.append(metrics(self.world))

    def register_action(self, action_id, handler):
        if not isinstance(action_id, str) or not action_id or action_id in self.actions or not callable(handler):
            raise ValueError(f"Invalid or duplicate action: {action_id}")
        self.actions[action_id] = handler

    def register_system(self, system: System):
        if not system.id or system.phase not in PHASES or not callable(system.update):
            raise ValueError("Invalid system contract")
        if any(existing.id == system.id for existing in self.systems):
            raise ValueError(f"Duplicate system: {system.id}")
        self.systems.append(system)
        self.world.system_ids = [item.id for item in self.systems]

    def step(self, count=1) -> World:
        if type(count) is not int or not 1 <= count <= 1000:
            raise ValueError("Step count must be between 1 and 1000")
        context = Context(self.world, lambda: random(self.world),
                          lambda **details: emit(self.world, **details),
                          lambda agent, decision: perform_action(self.world, self.actions, agent, decision))
        for _ in range(count):
            self.world.tick += 1
            for phase in PHASES:
                for system in sorted((s for s in self.systems if s.phase == phase), key=lambda s: (s.order, s.id)):
                    system.update(context)
        return self.world

    def set_condition(self, key: str, value: float):
        if key not in ("abundance", "social_safety", "pressure") or type(value) not in (int, float) or not isfinite(value) or not 0 <= value <= 1:
            raise ValueError("Invalid world condition")
        before = getattr(self.world.settings, key)
        setattr(self.world.settings, key, value)
        wire_key = "socialSafety" if key == "social_safety" else key
        emit(self.world, kind="intervention", visibility="private", text="شرایط جهان به دست ناظر تغییر کرد.", change={"key": wire_key, "before": before, "after": value})

    def announce_achievement(self, agent_id: str):
        agent = self.world.person(agent_id)
        if agent is None:
            raise ValueError("Agent not found")
        agent.needs.esteem = clamp(agent.needs.esteem + .15)
        agent.emotions.joy = clamp(agent.emotions.joy + .2)
        for observer in self.world.agents:
            observer.last_reaction_tick = -1
        event = emit(self.world, kind="achievement", visibility="public", actor_id=agent_id,
                     location_id=agent.location_id, text=f"خبر پیشرفت {agent.identity.name} در جمع منتشر شد.", origin="observer")
        queued = self.world.pending_events
        self.world.pending_events = [event]
        observe_events(self.world)
        self.world.pending_events = [item for item in queued if item.id != event.id]
        return event

    def snapshot(self) -> str:
        return dumps(self.world)

    @classmethod
    def from_snapshot(cls, text, *, systems=(), actions=None):
        world = loads(text)
        required = world.system_ids[:]
        simulation = cls(population=len(world.agents), world=world, systems=systems, actions=actions)
        if set(required) != set(world.system_ids):
            raise ValueError("This world requires a different set of systems")
        return simulation
