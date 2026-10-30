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
        candidate("rest", [("کمبود انرژی", (1 - n.energy) * 1.6), ("زمان استراحت", .55 if night else 0), ("شکیبایی", t.patience * .06)]),
        candidate("reflect", [("فشار عاطفی", (e.anxiety + e.sadness) * .5), ("میل به شناخت", t.openness * .2), ("خویشتن‌داری", t.self_control * .1), ("پردازش مقایسه با دیگران", e.envy * t.self_control * .2)]),
        candidate("create", [("ارزش پیشرفت", v.achievement * t.ambition * .7), ("نیاز به توانمندی", (1 - n.esteem) * .65), ("انرژی در دسترس", n.energy * .25), ("انگیزه پس از مقایسه", e.envy * v.achievement * .3), ("فشار محیط", -world.settings.pressure * .2)]),
    ]
    if friend:
        options.append(candidate("connect", [("نیاز به تعلق", (1 - n.belonging) * .95), ("تمایل به معاشرت", t.sociability * .38), ("اعتماد آموخته‌شده", agent.beliefs.trust * .2), ("تجربهٔ این رابطه", (trust(friend) - .5) * .35), ("اضطراب", -e.anxiety * .18)], friend.id))
    if person_in_need:
        options.append(candidate("help", [("همدلی و مراقبت", t.empathy * v.care * .65), ("نیاز قابل مشاهدهٔ دیگری", visible_need(person_in_need) * .6), ("انرژی خود", n.energy * .12)], person_in_need.id))
    if rival and resentment(rival) > .12:
        options.append(candidate("confront", [("دلخوری از رابطه", resentment(rival) * .8), ("حساسیت به انصاف", v.fairness * e.anger * .5), ("خویشتن‌داری", -t.self_control * .25)], rival.id))
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
