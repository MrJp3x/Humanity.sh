// The Python engine and both interfaces share one versioned catalog.
import catalog from '../../humanity/data/catalog.json' with { type: 'json' };

export const {
  traitLabels, valueLabels, beliefLabels, emotionLabels, actionLabels,
  locations, actionLocations, firstNames, lastNames, roles, backgrounds,
} = catalog;
