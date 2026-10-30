"""The ordered lifecycle and builtin systems. New systems use the same contract."""

from dataclasses import dataclass
from typing import Callable

from .agents import mask_gap, wellbeing
from .decision import decide
from .emotion import decay
from .models import Agent, Decision, Metrics, World
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
    changed = world.extensions.pop("conditionsChanged", False)
    for agent in world.agents:
        n, e, t, settings = agent.needs, agent.emotions, agent.traits, world.settings
        n.energy = clamp(n.energy - .025 - settings.pressure * .015)
        n.belonging = clamp(n.belonging - .012 - t.sociability * .01)
        n.esteem = clamp(n.esteem - .009)
        attainable_safety = settings.social_safety * .7 + settings.abundance * .3
        n.safety = clamp(n.safety + (attainable_safety - n.safety) * .04)
        decay(e)
        if hour < 7 or hour > 22:
            n.energy = clamp(n.energy - .025)
        # Residents experience their own conditions, rather than receiving a
        # global mood increment. Reappraise every four hours or after a change.
        if changed or world.tick % 4 == 0:
            context.emit(kind="living_conditions", visibility="private", target_id=agent.id,
                         text="شرایط فعلی زندگی: امکانات، امنیت و فشار روزمره.",
                         change={"abundance": settings.abundance, "socialSafety": settings.social_safety, "pressure": settings.pressure})


def take_actions(context: Context):
    for agent in shuffle(context.world, context.world.agents):
        context.act(agent, decide(context.world, agent))


def metrics(world: World) -> Metrics:
    agents = world.agents
    relations = [relation for agent in agents for relation in agent.relationships.values()]
    return Metrics(world.tick, mean(wellbeing(a) for a in agents),
                   mean(r.trust for r in relations) if relations else mean(a.beliefs.trust for a in agents),
                   mean(mask_gap(a) for a in agents), len([r for r in relations if r.familiarity > .1]),
                   *(mean(getattr(a.emotions, key) for a in agents) for key in ("joy", "sadness", "fear", "anger", "disgust")))


def develop(context: Context):
    world = context.world
    for agent in world.agents:
        learned_trust = agent.beliefs.trust - .5
        agent.traits.sociability = clamp(agent.traits.sociability + learned_trust * .0008, .05, .95)
        agent.traits.self_control = clamp(agent.traits.self_control + (-.0002 if agent.emotions.fear > .6 else .0001), .05, .95)
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
