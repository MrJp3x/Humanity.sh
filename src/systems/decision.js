import { mean, pick, random, shuffle } from '../core/random.js';
import { relationship } from '../domain/agent.js';

function candidate(id, factors, targetId = null) {
  return { id, targetId, factors: factors.map(([label, value]) => ({ label, value })), score: factors.reduce((sum, [, value]) => sum + value, 0) };
}

// Utility factors are an explicit, inspectable model assumption, not a fitted psychology model.
export function decide(world, agent) {
  const others = world.agents.filter(other => other.id !== agent.id);
  const acquaintances = others.filter(other => agent.relationships[other.id]);
  const pool = shuffle(world, acquaintances.length ? acquaintances : others).slice(0, 8);
  const friend = [...pool].sort((a, b) => (agent.relationships[b.id]?.trust ?? .5) - (agent.relationships[a.id]?.trust ?? .5))[0];
  // Other people's internal needs are not available to this agent. Use outward cues.
  const visibleNeed = other => Math.max(0, .75 - other.publicState.warmth);
  const personInNeed = [...pool].sort((a, b) => visibleNeed(b) - visibleNeed(a))[0];
  const rival = [...pool].sort((a, b) => (agent.relationships[b.id]?.resentment ?? 0) - (agent.relationships[a.id]?.resentment ?? 0))[0];
  const t = agent.traits, n = agent.needs, v = agent.values, e = agent.emotions;
  const night = ((8 + world.tick) % 24) < 7 || ((8 + world.tick) % 24) > 22;
  const options = [
    candidate('rest', [['کمبود انرژی', (1 - n.energy) * 1.6], ['زمان استراحت', night ? .55 : 0], ['شکیبایی', t.patience * .06]]),
    candidate('reflect', [['فشار عاطفی', (e.anxiety + e.sadness) * .5], ['میل به شناخت', t.openness * .2], ['خویشتن‌داری', t.selfControl * .1], ['پردازش مقایسه با دیگران', e.envy * t.selfControl * .2]]),
    candidate('create', [['ارزش پیشرفت', v.achievement * t.ambition * .7], ['نیاز به توانمندی', (1 - n.esteem) * .65], ['انرژی در دسترس', n.energy * .25], ['انگیزه پس از مقایسه', e.envy * v.achievement * .3], ['فشار محیط', -world.settings.pressure * .2]]),
  ];
  if (friend) options.push(candidate('connect', [['نیاز به تعلق', (1 - n.belonging) * .95], ['تمایل به معاشرت', t.sociability * .38], ['اعتماد آموخته‌شده', agent.beliefs.trust * .2], ['تجربهٔ این رابطه', ((agent.relationships[friend.id]?.trust ?? .5) - .5) * .35], ['اضطراب', -e.anxiety * .18]], friend.id));
  if (personInNeed) options.push(candidate('help', [['همدلی و مراقبت', t.empathy * v.care * .65], ['نیاز قابل مشاهدهٔ دیگری', visibleNeed(personInNeed) * .6], ['انرژی خود', n.energy * .12]], personInNeed.id));
  if (rival && (agent.relationships[rival.id]?.resentment ?? 0) > .12) options.push(candidate('confront', [['دلخوری از رابطه', relationship(agent, rival.id).resentment * .8], ['حساسیت به انصاف', v.fairness * e.anger * .5], ['خویشتن‌داری', -t.selfControl * .25]], rival.id));
  for (const option of options) {
    const variation = random(world) * .19;
    option.factors.push({ label: 'تنوع انتخاب', value: variation });
    option.score += variation;
  }
  options.sort((a, b) => b.score - a.score);
  const chosen = options[0];
  const related = agent.memories.filter(memory => memory.subjectId === chosen.targetId || (chosen.id === 'reflect' && memory.source === 'experience')).slice(-3);
  const decision = { tick: world.tick, actionId: chosen.id, targetId: chosen.targetId, score: chosen.score, factors: chosen.factors, alternatives: options.slice(1, 4).map(({ id, score }) => ({ id, score })), memoryIds: related.map(memory => memory.id) };
  agent.lastDecision = decision;
  return decision;
}

export const decisionSystem = {
  id: 'decision', phase: 'act', order: 10,
  update({ world, act }) {
    // Shuffled turn order prevents a fixed identifier from always acting first.
    for (const agent of shuffle(world, world.agents)) act(agent, decide(world, agent));
  },
};
