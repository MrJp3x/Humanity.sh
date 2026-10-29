import { clamp, pick, range } from '../core/random.js';
import { firstNames, lastNames, roles, backgrounds, traitLabels, valueLabels, locations } from './catalog.js';

export function createAgent(world, index) {
  const background = pick(world, backgrounds);
  const traits = Object.fromEntries(Object.keys(traitLabels).map(key => [key, range(world, .15, .90)]));
  const values = Object.fromEntries(Object.keys(valueLabels).map(key => [key, range(world, .2, .95)]));
  const location = locations[index % locations.length];
  const familyIndex = (index + Math.floor(index / firstNames.length)) % lastNames.length;
  const name = `${firstNames[index % firstNames.length]} ${lastNames[familyIndex]}`;
  return {
    id: `person-${index + 1}`,
    identity: { name, age: Math.floor(range(world, 19, 63)), role: pick(world, roles), background: background.story },
    traits, initialTraits: { ...traits }, values,
    beliefs: { trust: clamp(.5 + background.trust + range(world, -.08, .08)), fairness: clamp(.5 + background.fairness), selfWorth: range(world, .35, .8) },
    needs: { energy: range(world, .5, .95), belonging: range(world, .3, .8), safety: range(world, .45, .85), esteem: range(world, .35, .8) },
    emotions: { joy: range(world, .2, .55), anxiety: range(world, .05, .3), envy: range(world, .01, .15), anger: .02, sadness: .08 },
    goals: { immediate: 'پیدا کردن یک فعالیت معنادار', longTerm: values.achievement > values.belonging ? 'رشد و ساختن چیزی ارزشمند' : 'پیدا کردن رابطه‌های ماندگار' },
    relationships: {},
    memories: [{ id: `origin-${index}`, tick: 0, source: 'background', kind: 'formative', text: background.memory, interpretation: 'بخشی از پیشینهٔ اولیهٔ من است.', subjectId: null, importance: .8 }],
    lastDecision: null,
    publicState: { action: 'reflect', text: 'در حال آشنا شدن با جهان', warmth: .5 },
    locationId: location.id,
    position: { x: clamp(location.x + range(world, -.10, .10), .06, .94), y: clamp(location.y + range(world, -.1, .1), .08, .92) },
    extensions: {},
  };
}

export function relationship(agent, otherId) {
  return agent.relationships[otherId] ??= { trust: .5, affection: .45, resentment: 0, familiarity: 0 };
}
export function remember(agent, entry, world) {
  const memory = { id: `m-${world.tick}-${agent.id}-${world.nextMemoryId++}`, tick: world.tick, importance: .5, source: 'experience', ...entry };
  agent.memories.push(memory);
  // The simulation retains a bounded recent memory window plus formative memories.
  // This is explicit storage truncation, not a claim to model human forgetting.
  if (agent.memories.length > 82) agent.memories.splice(1, agent.memories.length - 82);
  return memory;
}
export function wellbeing(agent) {
  const n = agent.needs;
  return clamp((n.energy + n.belonging + n.safety + n.esteem) / 4 + agent.emotions.joy * .12 - agent.emotions.anxiety * .12 - agent.emotions.sadness * .1);
}
export function maskGap(agent) {
  return clamp(agent.publicState.warmth - (agent.emotions.joy - agent.emotions.envy * .65 - agent.emotions.anger * .6));
}
