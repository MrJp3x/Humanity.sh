import { clamp } from '../core/random.js';

export const needsSystem = {
  id: 'needs', phase: 'before', order: 10,
  update({ world }) {
    const hour = (8 + world.tick) % 24;
    for (const agent of world.agents) {
      agent.needs.energy = clamp(agent.needs.energy - .025 - world.settings.pressure * .015);
      agent.needs.belonging = clamp(agent.needs.belonging - .012 - agent.traits.sociability * .01);
      agent.needs.esteem = clamp(agent.needs.esteem - .009);
      agent.needs.safety = clamp(agent.needs.safety + (world.settings.socialSafety - .5) * .012 + (world.settings.abundance - .5) * .012);
      for (const key of Object.keys(agent.emotions)) agent.emotions[key] *= key === 'envy' ? .95 : .90;
      agent.emotions.anxiety = clamp(agent.emotions.anxiety + (1 - agent.needs.safety) * agent.traits.sensitivity * .025 + world.settings.pressure * .018);
      if (hour < 7 || hour > 22) agent.needs.energy = clamp(agent.needs.energy - .025);
    }
  },
};
