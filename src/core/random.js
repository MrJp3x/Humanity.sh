// All simulation randomness passes through this serializable generator.
// Rendering is deliberately outside this stream so frame rate cannot change history.
export function hashSeed(seed) {
  let h = 2166136261;
  for (const char of String(seed)) h = Math.imul(h ^ char.charCodeAt(0), 16777619);
  return h >>> 0;
}
export function random(world) {
  world.rng = (world.rng + 0x6D2B79F5) >>> 0;
  let t = world.rng;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}
export const range = (world, min, max) => min + random(world) * (max - min);
export const pick = (world, items) => items[Math.floor(random(world) * items.length)];
export const clamp = (value, min = 0, max = 1) => Math.max(min, Math.min(max, value));
export const mean = values => values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;
export function shuffle(world, items) {
  const result = [...items];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(random(world) * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}
