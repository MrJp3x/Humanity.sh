"""A small, explicit utility policy. Weights are model assumptions, not diagnoses."""

from dataclasses import dataclass

from .models import Agent, Alternative, Decision, Factor, World
from .randomness import random, shuffle


@dataclass
class Candidate:
    id: str
    factors: list[Factor]
    target_id: str | None = None
    score: float = 0.0


def candidate(action_id, factors, target_id=None) -> Candidate:
    score = 0.0
    for _, value in factors:
        score += value
    return Candidate(action_id, [Factor(*f) for f in factors], target_id, score)


def decide(world: World, agent: Agent) -> Decision:
    others = [other for other in world.agents if other.id != agent.id]
    acquaintances = [other for other in others if other.id in agent.relationships]
    pool = shuffle(world, acquaintances or others)[:8]

    def trust(other):
        relation = agent.relationships.get(other.id)
        return relation.trust if relation else .5

    def resentment(other):
        relation = agent.relationships.get(other.id)
        return relation.resentment if relation else 0

    def visible_need(other):
        # Other people's private needs are deliberately inaccessible here.
        return max(0, .75 - other.public_state.warmth)

    friend = max(pool, key=trust) if pool else None
    person_in_need = max(pool, key=visible_need) if pool else None
    rival = max(pool, key=resentment) if pool else None
    t, n, v, e = agent.traits, agent.needs, agent.values, agent.emotions
    hour = (8 + world.tick) % 24
    night = hour < 7 or hour > 22
    options = [
        candidate("rest", [("کمبود انرژی", (1 - n.energy) * 1.6), ("زمان استراحت", .55 if night else 0), ("نیاز به آرامش پس از ترس", e.fear * (1 - agent.beliefs.trust) * .5)]),
        candidate("reflect", [("فشار عاطفی", (e.fear + e.sadness + e.disgust) * .5), ("میل به شناخت", t.openness * .2), ("تنظیم خشم با خویشتن‌داری", e.anger * t.self_control * .6)]),
        candidate("create", [("ارزش پیشرفت", v.achievement * t.ambition * .7), ("نیاز به توانمندی", (1 - n.esteem) * .65), ("انرژی در دسترس", n.energy * .25), ("انگیزه و شادی", e.joy * .2), ("فشار محیط", -world.settings.pressure * .2), ("ترس از موقعیت", -e.fear * .35)]),
    ]
    if friend:
        options.append(candidate("connect", [("نیاز به تعلق", (1 - n.belonging) * .95), ("تمایل به معاشرت", t.sociability * .38), ("اعتماد آموخته‌شده", agent.beliefs.trust * .2), ("تجربهٔ این رابطه", (trust(friend) - .5) * .65), ("جست‌وجوی حمایت در غم", e.sadness * agent.beliefs.trust * .3), ("ترس و فاصله گرفتن", -e.fear * (1 - trust(friend)) * .6), ("بیزاری از رفتارها", -e.disgust * .35)], friend.id))
    if person_in_need:
        options.append(candidate("help", [("همدلی و مراقبت", t.empathy * v.care * .65), ("نیاز قابل مشاهدهٔ دیگری", visible_need(person_in_need) * .6), ("انرژی خود", n.energy * .12), ("ترس و محدودیت توان کمک", -e.fear * .3)], person_in_need.id))
    if rival and resentment(rival) > .12:
        options.append(candidate("confront", [("دلخوری از رابطه", resentment(rival) * .8), ("خشم و اعتراض", e.anger * (1 + v.fairness * .5)), ("خویشتن‌داری", -t.self_control * .25), ("ترس از رویارویی", -e.fear * .5), ("بیزاری و دوری", -e.disgust * .3)], rival.id))
    for option in options:
        variation = random(world) * .19
        option.factors.append(Factor("تنوع انتخاب", variation))
        option.score += variation
    options.sort(key=lambda option: -option.score)
    chosen = options[0]
    related = [memory for memory in agent.memories if memory.subject_id == chosen.target_id or (chosen.id == "reflect" and memory.source == "experience")][-3:]
    decision = Decision(world.tick, chosen.id, chosen.target_id, chosen.score, chosen.factors,
                        [Alternative(option.id, option.score) for option in options[1:4]], [m.id for m in related])
    agent.last_decision = decision
    return decision
