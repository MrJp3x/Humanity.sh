import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { renderAgentDetail, renderExperiment, renderMetrics } from '../src/ui/render.js';

// Exercise the real Python-to-HTML contract without controlling a desktop UI.
const fixture = JSON.parse(execFileSync(process.env.HUMANITY_PYTHON ?? 'python3', ['-c', `
import json, tempfile
from pathlib import Path
from humanity.application import ApplicationController
with tempfile.TemporaryDirectory() as directory:
    app = ApplicationController(Path(directory), fresh=True)
    app.handle('encounter', {'kind': 'insult', 'actorId': 'person-1', 'targetId': 'person-2'})
    app.handle('inspect', {'id': 'person-2'})
    print(json.dumps(app.state(), ensure_ascii=False))
`], { encoding: 'utf8' }));

test('Python five-feeling projections render causal traces and complete experiment results', () => {
  const world = fixture.world;
  const person = world.agents.find(a => a.id === 'person-2');
  const detail = renderAgentDetail(world, person, 'mind');
  const experiment = renderExperiment(world, fixture.experimentId);
  const metrics = renderMetrics(world);
  for (const label of ['شادی', 'غم', 'ترس', 'خشم', 'انزجار']) {
    assert.ok(detail.includes(label));
    assert.ok(experiment.includes(label));
    assert.ok(metrics.includes(label));
  }
  assert.ok(detail.includes('چرا این واکنش را نشان داد؟'));
  assert.ok(detail.includes('→'));
  assert.ok(detail.includes('واکنش:'));
  assert.ok(metrics.includes('میانگین احساس جامعه'));
  assert.doesNotMatch(detail + experiment + metrics, /NaN|undefined|اضطراب|حسادت/);
});
