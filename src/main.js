import { connectEngine } from './services/engine-client.js';
import { shell } from './ui/shell.js';
import { WorldMap } from './ui/world-map.js';
import { renderMetrics, renderAgentHeader, renderAgentDetail, renderFeed, renderPeople, renderConditions, renderExperiment } from './ui/render.js';
import { icon } from './ui/icons.js';
import { dayTime, number, percent, escape as esc } from './ui/format.js';

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
$('#app').innerHTML = shell();
let engine;
try {
  engine = await connectEngine();
} catch(error) {
  $('#app').innerHTML = `<main><div class="notice"><h1>ارتباط با موتور برقرار نشد</h1><p>${esc(error.message)}</p><p>برنامه را از طریق python -m humanity.desktop اجرا کن.</p></div></main>`;
  throw error;
}
let state = engine.state;
let world = state.world;
let selectedId = state.selectedId;
let generation = state.generation;
let tab = 'mind', view = 'observatory', toastTimer;
const map = new WorldMap($('#world-canvas'), {
  getWorld: () => world, getSelected: () => selectedId,
  onSelect: id => safe(() => selectAgent(id)), tooltip: $('#map-tooltip'),
});
$('.version').textContent = 'v0.2';
if (engine.mode === 'desktop') {
  $('.local-badge').innerHTML = '<i></i> نسخهٔ دسکتاپ · روی این دستگاه';
  $('#save-button').innerHTML = `${icon('save',16)} ذخیره روی این دستگاه`;
  const about = document.createElement('p');
  about.className = 'notice';
  about.textContent = 'موتور این نسخه با پایتون اجرا می‌شود. جهان در پس‌زمینه به زندگی ادامه می‌دهد؛ هنگام بستن برنامه، نشست فعلی خودکار ذخیره می‌شود. ذخیرهٔ دستی برای مقایسهٔ دو آینده جدا نگه داشته می‌شود.';
  $('#about-dialog').querySelector('.field-note').replaceWith(about);
}

function toast(message, error = false) {
  if (!message) return;
  clearTimeout(toastTimer);
  $('#toast').textContent = message;
  $('#toast').className = `visible${error ? ' error' : ''}`;
  toastTimer = setTimeout(() => $('#toast').className = '', 4500);
}
async function safe(operation) {
  try { return await operation(); }
  catch(error) { console.error(error); toast(error.message || 'فرمان اجرا نشد؛ وضعیت فعلی حفظ شد.', true); }
}
async function command(method, args = {}) {
  const result = await engine.command(method, args);
  if (result.message) toast(result.message);
  return result;
}
function selectedAgent() { return world.agents.find(a => a.id === selectedId) ?? world.agents[0]; }
function render() {
  $('#metrics').innerHTML = renderMetrics(world);
  $('#world-time').textContent = dayTime(world.tick);
  $('#running-label').textContent = state.running ? 'در جریان' : 'متوقف';
  $('#running-label').classList.toggle('paused', !state.running);
  $('#play-button').innerHTML = `${icon(state.running ? 'pause' : 'play',15)} ${state.running ? 'توقف زمان' : 'ادامهٔ زندگی'}`;
  $('#step-button').disabled = state.running;
  $$('[data-speed]').forEach(b => { const active=Number(b.dataset.speed)===state.speed;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active)); });
  $('#map-count').textContent = `${number(world.agents.length)} زندگی در جریان`;
  $('#agent-header').innerHTML = renderAgentHeader(selectedAgent());
  const detailScroll = $('#agent-detail').scrollTop;
  $('#agent-detail').innerHTML = renderAgentDetail(world,selectedAgent(),tab);
  $('#agent-detail').scrollTop = detailScroll;
  const feedScroll = $('#event-feed').scrollTop;
  $('#event-feed').innerHTML = renderFeed(world,$('#event-filter').value,selectedId);
  $('#event-feed').scrollTop = feedScroll;
  if(view==='people')$('#people-grid').innerHTML=renderPeople(world,$('#people-search').value);
  if(view==='experiments')$('#experiment-results').innerHTML=renderExperiment(world,state.experimentId);
}
function renderConditionsControls() {
  $('#modal-conditions').innerHTML=renderConditions(world);
  $('#inline-conditions').innerHTML=renderConditions(world);
}
function renderExperimentPeople() {
  const previous=$('#achievement-person').value;
  $('#achievement-person').innerHTML=world.agents.map(a=>`<option value="${a.id}">${esc(a.identity.name)}</option>`).join('');
  $('#achievement-person').value=world.agents.some(a=>a.id===previous)?previous:selectedId;
}
function setTab(nextTab) {
  tab=nextTab;
  $$('[data-tab]').forEach(b=>{const active=b.dataset.tab===tab;b.classList.toggle('active',active);b.setAttribute('aria-selected',String(active));});
  $('#agent-detail').scrollTop=0;
}
function receive(next) {
  const changed=next.generation!==generation;
  const selectedChanged=next.selectedId!==selectedId;
  state=next;world=next.world;selectedId=next.selectedId;
  if(changed){generation=next.generation;setTab('mind');map.reset();renderConditionsControls();renderExperimentPeople();}
  if(selectedChanged)$('#agent-detail').scrollTop=0;
  render();
  if(next.error)toast(next.error,true);
}
engine.subscribe(receive);
async function selectAgent(id) {
  if(!world.agents.some(a=>a.id===id))return;
  await command('inspect',{id});
  if(view!=='observatory')switchView('observatory');
  if(matchMedia('(max-width:760px)').matches)$('.inspector').scrollIntoView({behavior:'smooth',block:'start'});
}
function switchView(nextView) {
  view=nextView;
  ['observatory','people','experiments'].forEach(id=>$(`#${id}-view`).classList.toggle('hidden',id!==view));
  $$('[data-view]').forEach(button=>{button.classList.toggle('active',button.dataset.view===view);button.setAttribute('aria-current',button.dataset.view===view?'page':'false');});
  if(view==='experiments'){renderExperimentPeople();renderConditionsControls();}
  render();
  if(view==='observatory')requestAnimationFrame(()=>map.resize());
}

document.addEventListener('click',event=>{
  const button=event.target.closest('button');
  if(!button)return;
  safe(async()=>{
    if(button.dataset.view)switchView(button.dataset.view);
    if(button.dataset.agent)await selectAgent(button.dataset.agent);
    if(button.dataset.tab){setTab(button.dataset.tab);render();}
    if(button.dataset.speed)await command('speed',{value:Number(button.dataset.speed)});
    if(button.dataset.event){
      const record=world.events.find(e=>e.id===button.dataset.event);
      if(record?.actorId){await command('inspect',{id:record.actorId});setTab('memories');render();}
    }
    if(button.hasAttribute('data-close-dialog'))button.closest('dialog').close();
  });
});
$('#play-button').addEventListener('click',()=>safe(()=>command('run',{value:!state.running})));
$('#step-button').addEventListener('click',()=>safe(()=>command('step')));
$('#new-world').addEventListener('click',()=>{$('#population-input').value=String(world.agents.length);$('#seed-input').value=world.seed;$('#world-dialog').showModal();});
$('#world-form').addEventListener('submit',event=>{
  event.preventDefault();
  safe(async()=>{await command('new_world',{seed:$('#seed-input').value.trim(),population:Number($('#population-input').value)});$('#world-dialog').close();toast('جهان تازه خلق شد.');});
});
$('#conditions-button').addEventListener('click',()=>{renderConditionsControls();$('#conditions-dialog').showModal();});
$('#about-button').addEventListener('click',()=>$('#about-dialog').showModal());
$('#event-filter').addEventListener('change',()=>$('#event-feed').innerHTML=renderFeed(world,$('#event-filter').value,selectedId));
$('#people-search').addEventListener('input',()=>$('#people-grid').innerHTML=renderPeople(world,$('#people-search').value));
$('#color-mode').addEventListener('change',event=>{map.mode=event.target.value;$('.map-legend').querySelectorAll('span:not(.map-count)').forEach(s=>s.style.display=map.mode==='mood'?'flex':'none');});
$('#links-toggle').addEventListener('click',()=>{map.showLinks=!map.showLinks;$('#links-toggle').classList.toggle('selected',map.showLinks);$('#links-toggle').setAttribute('aria-pressed',String(map.showLinks));});
document.addEventListener('input',event=>{
  if(event.target.dataset.condition)$$(`[data-condition-value="${event.target.dataset.condition}"]`).forEach(el=>el.textContent=percent(Number(event.target.value)/100));
});
document.addEventListener('change',event=>{
  const key=event.target.dataset.condition;if(!key)return;
  safe(async()=>{await command('condition',{key,value:Number(event.target.value)/100});$$(`[data-condition="${key}"]`).forEach(el=>el.value=event.target.value);toast('شرایط جهان تغییر کرد.');});
});
$('#announce-button').addEventListener('click',()=>safe(async()=>{await command('achievement',{id:$('#achievement-person').value});$('#experiment-results').scrollIntoView({behavior:'smooth',block:'start'});toast('خبر منتشر شد. برداشت شاهدان را مقایسه کن.');}));
$('#save-button').addEventListener('click',()=>safe(()=>command('save')));
$('#load-button').addEventListener('click',()=>safe(()=>command('load')));
$('#export-button').addEventListener('click',()=>safe(async()=>{
  if(engine.mode==='desktop'){await command('export');return;}
  const {snapshot}=await command('snapshot');
  const url=URL.createObjectURL(new Blob([snapshot],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download=`humanity-world-${world.tick}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}));
$('#import-button').addEventListener('click',()=>safe(async()=>{if(engine.mode==='desktop')await command('open');else $('#snapshot-file').click();}));
$('#snapshot-file').addEventListener('change',event=>safe(async()=>{
  const file=event.target.files[0];if(!file)return;
  try{if(file.size>=32_000_000)throw new Error('فایل جهان بزرگ‌تر از حد مجاز است.');await command('import',{text:await file.text()});toast('جهان از فایل باز شد.');}
  finally{event.target.value='';}
}));
document.addEventListener('keydown',event=>{
  if(event.code==='Space'&&!['INPUT','SELECT','TEXTAREA','BUTTON'].includes(document.activeElement?.tagName)&&!$('dialog[open]')){event.preventDefault();safe(()=>command('run',{value:!state.running}));}
});
renderConditionsControls();renderExperimentPeople();render();
if(state.startupNote)toast(state.startupNote);
