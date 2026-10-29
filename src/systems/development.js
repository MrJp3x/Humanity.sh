import { clamp, mean } from '../core/random.js';
import { wellbeing, maskGap } from '../domain/agent.js';

export function metrics(world) {
  const agents = world.agents;
  const relations = agents.flatMap(agent => Object.values(agent.relationships));
  return {
    tick: world.tick, wellbeing: mean(agents.map(wellbeing)),
    trust: relations.length ? mean(relations.map(r => r.trust)) : mean(agents.map(a => a.beliefs.trust)),
    gap: mean(agents.map(maskGap)),
    connections: relations.filter(r => r.familiarity > .1).length,
    joy: mean(agents.map(a => a.emotions.joy)),
    anxiety: mean(agents.map(a => a.emotions.anxiety)),
    envy: mean(agents.map(a => a.emotions.envy)),
  };
}

export const developmentSystem = {
  id: 'development', phase: 'after', order: 10,
  update({ world }) {
    for (const agent of world.agents) {
      // Small, bounded changes across repeated experience; a single event cannot rewrite a person.
      const learnedTrust = agent.beliefs.trust - .5;
      agent.traits.sociability = clamp(agent.traits.sociability + learnedTrust * .0008, .05, .95);
      agent.traits.selfControl = clamp(agent.traits.selfControl + (agent.emotions.anxiety > .6 ? -.0002 : .0001), .05, .95);
      for (const rel of Object.values(agent.relationships)) rel.resentment *= .998;
      const n = agent.needs;
      agent.goals.immediate = n.energy < .3 ? 'بازیابی انرژی و استراحت' : n.belonging < .4 ? 'پیدا کردن همراه و حس تعلق' : n.esteem < .4 ? 'به دست آوردن حس توانمندی' : 'دنبال کردن علایق و رابطه‌ها';
    }
    world.history.push(metrics(world));
    if (world.history.length > 240) world.history.shift();
  },
};
