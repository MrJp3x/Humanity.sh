"""The ordered lifecycle and builtin systems. New systems use the same contract."""

from dataclasses import dataclass, fields
from typing import Callable

from .agents import mask_gap, wellbeing
from .decision import decide
from .models import Agent, Decision, Emotions, Metrics, World
from .perception import observe_events
from .randomness import clamp, mean, shuffle

PHASES = ("before", "act", "observe", "after")


@dataclass
class Context:
    world: World
    random: Callable[[], float]
    emit: Callable
    act: Callable[[Agent, Decision], None]


@dataclass(frozen=True)
class System:
    id: str
    phase: str
    update: Callable[[Context], None]
    order: int = 10


def update_needs(context: Context):
    world = context.world
    hour = (8 + world.tick) % 24
    for agent in world.agents:
        n, e, t, settings = agent.needs, agent.emotions, agent.traits, world.settings
        n.energy = clamp(n.energy - .025 - settings.pressure * .015)
        n.belonging = clamp(n.belonging - .012 - t.sociability * .01)
        n.esteem = clamp(n.esteem - .009)
        n.safety = clamp(n.safety + (settings.social_safety - .5) * .012 + (settings.abundance - .5) * .012)
        for f in fields(Emotions):
            setattr(e, f.name, getattr(e, f.name) * (.95 if f.name == "envy" else .90))
        e.anxiety = clamp(e.anxiety + (1 - n.safety) * t.sensitivity * .025 + settings.pressure * .018)
        if hour < 7 or hour > 22:
            n.energy = clamp(n.energy - .025)


def take_actions(context: Context):
    for agent in shuffle(context.world, context.world.agents):
        context.act(agent, decide(context.world, agent))


def metrics(world: World) -> Metrics:
    agents = world.agents
    relations = [relation for agent in agents for relation in agent.relationships.values()]
    return Metrics(world.tick, mean(wellbeing(a) for a in agents),
                   mean(r.trust for r in relations) if relations else mean(a.beliefs.trust for a in agents),
                   mean(mask_gap(a) for a in agents), len([r for r in relations if r.familiarity > .1]),
                   mean(a.emotions.joy for a in agents), mean(a.emotions.anxiety for a in agents), mean(a.emotions.envy for a in agents))


def develop(context: Context):
    world = context.world
    for agent in world.agents:
        learned_trust = agent.beliefs.trust - .5
        agent.traits.sociability = clamp(agent.traits.sociability + learned_trust * .0008, .05, .95)
        agent.traits.self_control = clamp(agent.traits.self_control + (-.0002 if agent.emotions.anxiety > .6 else .0001), .05, .95)
        for relation in agent.relationships.values():
            relation.resentment *= .998
        n = agent.needs
        agent.goals.immediate = "بازیابی انرژی و استراحت" if n.energy < .3 else "پیدا کردن همراه و حس تعلق" if n.belonging < .4 else "به دست آوردن حس توانمندی" if n.esteem < .4 else "دنبال کردن علایق و رابطه‌ها"
    world.history.append(metrics(world))
    if len(world.history) > 240:
        del world.history[0]


BUILTIN_SYSTEMS = (
    System("needs", "before", update_needs),
    System("decision", "act", take_actions),
    System("perception", "observe", lambda context: observe_events(context.world)),
    System("development", "after", develop),
)
