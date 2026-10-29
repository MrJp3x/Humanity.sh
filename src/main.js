import { Simulation } from './core/simulation.js';
import { shell } from './ui/shell.js';
import { WorldMap } from './ui/world-map.js';
import { renderMetrics, renderAgentHeader, renderAgentDetail, renderFeed, renderPeople, renderConditions, renderExperiment } from './ui/render.js';
import { icon } from './ui/icons.js';
import { dayTime, number, percent, escape as esc } from './ui/format.js';

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const SAVE_KEY = 'humanity.sh/world/v1';
let simulation = new Simulation();
// Start with six actual simulated hours so the first view contains lived experience.
simulation.step(6);
let selectedId = simulation.world.agents[0].id;
let tab = 'mind', view = 'observatory', running = false, speed = 1, timer = null, experimentEvent = null;
let toastTimer;
$('#app').innerHTML = shell();
const map = new WorldMap($('#world-canvas'), { getWorld: () => simulation.world, getSelected: () => selectedId, onSelect: selectAgent, tooltip: $('#map-tooltip') });

function toast(message, error = false) {
  clearTimeout(toastTimer);
  $('#toast').textContent = message;
  $('#toast').className = `visible${error ? ' error' : ''}`;
  toastTimer = setTimeout(() => $('#toast').className = '', 4000);
}
function selectedAgent() { return simulation.world.agents.find(a => a.id === selectedId) ?? simulation.world.agents[0]; }
function render() {
  const world = simulation.world;
  $('#metrics').innerHTML = renderMetrics(world);
  $('#world-time').textContent = dayTime(world.tick);
  $('#running-label').textContent = running ? 'در جریان' : 'متوقف';
  $('#running-label').classList.toggle('paused', !running);
  $('#play-button').innerHTML = `${icon(running ? 'pause' : 'play', 15)} ${running ? 'توقف زمان' : 'ادامهٔ زندگی'}`;
  $('#step-button').disabled = running;
  $('#map-count').textContent = `${number(world.agents.length)} زندگی در جریان`;
  const agent = selectedAgent();
  $('#agent-header').innerHTML = renderAgentHeader(agent);
  $('#agent-detail').innerHTML = renderAgentDetail(world, agent, tab);
  $('#event-feed').innerHTML = renderFeed(world, $('#event-filter').value, selectedId);
  if (view === 'people') $('#people-grid').innerHTML = renderPeople(world, $('#people-search').value);
  if (view === 'experiments' && experimentEvent) $('#experiment-results').innerHTML = renderExperiment(world, experimentEvent);
}
function renderConditionControls() {
  $('#modal-conditions').innerHTML = renderConditions(simulation.world);
  $('#inline-conditions').innerHTML = renderConditions(simulation.world);
}
function renderExperimentPeople() {
  $('#achievement-person').innerHTML = simulation.world.agents.map(a => `<option value="${a.id}">${esc(a.identity.name)}</option>`).join('');
  $('#achievement-person').value = selectedId;
}
function selectAgent(id) {
  if (!simulation.world.agents.some(a => a.id === id)) return;
  selectedId = id;
  if (view !== 'observatory') switchView('observatory');
  render();
  if (matchMedia('(max-width:760px)').matches) $('.inspector').scrollIntoView({ behavior: 'smooth', block: 'start' });
}
function switchView(nextView) {
  view = nextView;
  ['observatory','people','experiments'].forEach(id => $(`#${id}-view`).classList.toggle('hidden', id !== view));
  $$('[data-view]').forEach(button => { button.classList.toggle('active', button.dataset.view === view); button.setAttribute('aria-current', button.dataset.view === view ? 'page' : 'false'); });
  if (view === 'people') $('#people-grid').innerHTML = renderPeople(simulation.world, $('#people-search').value);
  if (view === 'experiments') { renderExperimentPeople(); renderConditionControls(); $('#experiment-results').innerHTML = renderExperiment(simulation.world, experimentEvent); }
  if (view === 'observatory') requestAnimationFrame(() => map.resize());
}
function setRunning(value) {
  running = value;
  clearInterval(timer);
  if (running) timer = setInterval(() => {
    try { simulation.step(); render(); }
    catch(error) { setRunning(false); console.error(error); toast('اجرای جهان با خطا متوقف شد؛ وضعیت فعلی حفظ شده است.', true); }
  }, 1200 / speed);
  render();
}
function loadSimulation(nextSimulation) {
  setRunning(false);
  simulation = nextSimulation;
  selectedId = simulation.world.agents[0].id;
  tab = 'mind'; experimentEvent = null;
  $$('[data-tab]').forEach(button => { button.classList.toggle('active',button.dataset.tab===tab); button.setAttribute('aria-selected',String(button.dataset.tab===tab)); });
  map.reset();
  renderConditionControls(); renderExperimentPeople();
  $('#experiment-results').innerHTML='';
  render();
}
document.addEventListener('click', event => {
  const button = event.target.closest('button');
  if (!button) return;
  if (button.dataset.view) switchView(button.dataset.view);
  if (button.dataset.agent) selectAgent(button.dataset.agent);
  if (button.dataset.tab) {
    tab = button.dataset.tab;
    $$('[data-tab]').forEach(b => { b.classList.toggle('active',b===button); b.setAttribute('aria-selected',String(b===button)); });
    $('#agent-detail').innerHTML=renderAgentDetail(simulation.world,selectedAgent(),tab);
  }
  if (button.dataset.speed) {
    speed = Number(button.dataset.speed);
    $$('[data-speed]').forEach(b => { b.classList.toggle('active',b===button); b.setAttribute('aria-pressed',String(b===button)); });
    if (running) setRunning(true);
  }
  if (button.dataset.event) {
    const record = simulation.world.events.find(e=>e.id===button.dataset.event);
    if (record?.actorId) { selectedId=record.actorId;tab='memories';$$('[data-tab]').forEach(b=>{b.classList.toggle('active',b.dataset.tab===tab);b.setAttribute('aria-selected',String(b.dataset.tab===tab));});render(); }
  }
  if (button.hasAttribute('data-close-dialog')) button.closest('dialog').close();
});
$('#play-button').addEventListener('click',()=>setRunning(!running));
$('#step-button').addEventListener('click',()=>{simulation.step();render();});
$('#new-world').addEventListener('click',()=>{$('#population-input').value=String(simulation.world.agents.length);$('#seed-input').value=simulation.world.seed;$('#world-dialog').showModal();});
$('#world-form').addEventListener('submit',event=>{
  event.preventDefault();
  try {
    const next = new Simulation({ seed:$('#seed-input').value.trim(),population:Number($('#population-input').value) });
    next.step(6); loadSimulation(next); $('#world-dialog').close(); toast('جهان تازه خلق شد. هر فرد، یک شروع متفاوت دارد.');
  } catch { toast('تعداد افراد یا بذر جهان معتبر نیست.',true); }
});
$('#conditions-button').addEventListener('click',()=>{renderConditionControls();$('#conditions-dialog').showModal();});
$('#about-button').addEventListener('click',()=>$('#about-dialog').showModal());
$('#event-filter').addEventListener('change',()=>$('#event-feed').innerHTML=renderFeed(simulation.world,$('#event-filter').value,selectedId));
$('#people-search').addEventListener('input',()=>$('#people-grid').innerHTML=renderPeople(simulation.world,$('#people-search').value));
$('#color-mode').addEventListener('change',event=>{map.mode=event.target.value;$('.map-legend').querySelectorAll('span:not(.map-count)').forEach(s=>s.style.display=map.mode==='mood'?'flex':'none');});
$('#links-toggle').addEventListener('click',()=>{map.showLinks=!map.showLinks;$('#links-toggle').classList.toggle('selected',map.showLinks);$('#links-toggle').setAttribute('aria-pressed',String(map.showLinks));});
document.addEventListener('input',event=>{
  if (event.target.dataset.condition) $$(`[data-condition-value="${event.target.dataset.condition}"]`).forEach(el=>el.textContent=percent(Number(event.target.value)/100));
});
document.addEventListener('change',event=>{
  const key=event.target.dataset.condition;
  if(!key)return;
  simulation.setCondition(key,Number(event.target.value)/100);
  $$(`[data-condition="${key}"]`).forEach(el=>el.value=event.target.value);
  render();toast('شرایط جهان تغییر کرد؛ اثر آن با ادامهٔ زمان ظاهر می‌شود.');
});
$('#announce-button').addEventListener('click',()=>{
  setRunning(false);
  const event=simulation.announceAchievement($('#achievement-person').value);
  experimentEvent=event.id;render();
  $('#experiment-results').innerHTML=renderExperiment(simulation.world,event.id);
  $('#experiment-results').scrollIntoView({behavior:'smooth',block:'start'});
  toast('خبر منتشر شد. برداشت شخصی شاهدان را مقایسه کن.');
});
$('#save-button').addEventListener('click',()=>{try{localStorage.setItem(SAVE_KEY,simulation.snapshot());toast('جهان در این مرورگر ذخیره شد.');}catch{toast('فضای ذخیرهٔ مرورگر کافی نیست؛ دریافت فایل را امتحان کن.',true);}});
$('#load-button').addEventListener('click',()=>{
  try{const data=localStorage.getItem(SAVE_KEY);if(!data){toast('هنوز ذخیره‌ای در این مرورگر وجود ندارد.',true);return;}loadSimulation(Simulation.fromSnapshot(data));toast('جهان به آخرین ذخیره بازگشت.');}catch{toast('ذخیره قابل بازکردن نیست؛ جهان فعلی حفظ شده است.',true);}
});
$('#export-button').addEventListener('click',()=>{
  const url=URL.createObjectURL(new Blob([simulation.snapshot()],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download=`humanity-world-${simulation.world.tick}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
$('#import-button').addEventListener('click',()=>$('#snapshot-file').click());
$('#snapshot-file').addEventListener('change',async event=>{
  const file=event.target.files[0];if(!file)return;
  try{if(file.size>32_000_000)throw new Error('too large');const next=Simulation.fromSnapshot(await file.text());loadSimulation(next);toast('جهان از فایل باز شد.');}catch{toast('فایل جهان معتبر یا سازگار نیست؛ جهان فعلی حفظ شد.',true);}finally{event.target.value='';}
});
document.addEventListener('keydown',event=>{
  if(event.code==='Space'&&!['INPUT','SELECT','TEXTAREA','BUTTON'].includes(document.activeElement?.tagName)&&!$('dialog[open]')){event.preventDefault();setRunning(!running);}
});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&running)setRunning(false);});
renderConditionControls();renderExperimentPeople();render();
