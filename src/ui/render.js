import { wellbeing, maskGap } from '../domain/agent.js';
import { traitLabels, valueLabels, beliefLabels, emotionLabels, actionLabels } from '../domain/catalog.js';
import { metrics } from '../systems/development.js';
import { icon } from './icons.js';
import { escape as esc, number, percent, dayTime, initials, mood, kindLabels } from './format.js';

export function sparkline(values, color = '#c9ed8c') {
  if (!values.length) return '';
  const data = values.length === 1 ? [values[0], values[0]] : values;
  const points = data.map((value, i) => `${i / (data.length - 1) * 100},${30 - value * 26}`).join(' ');
  return `<svg class="sparkline" viewBox="0 0 100 34" preserveAspectRatio="none" aria-hidden="true"><polyline points="${points}" fill="none" stroke="${color}" stroke-width="1.6" vector-effect="non-scaling-stroke"/></svg>`;
}
function meter(label, value, color = 'green', extra = '') {
  return `<div class="meter-row"><div><span>${esc(label)}</span><span class="meter-value">${percent(value)}${extra}</span></div><div class="meter ${color}"><i style="width:${Math.max(0, Math.min(100, value * 100))}%"></i></div></div>`;
}
const emotionName = key => emotionLabels[key] ?? ({ anxiety: 'اضطرابِ مدل قبلی', envy: 'حسادتِ مدل قبلی' })[key] ?? key;
const traceNumber = new Intl.NumberFormat('fa-IR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const tracePercent = value => `${traceNumber.format(value * 100)}٪`;
function feelingsRow(feelings) {
  return Object.entries(feelings ?? {}).filter(([key]) => key !== 'suspicion').map(([key,value]) => `<span>${esc(emotionName(key))} <b>${percent(value)}</b></span>`).join('');
}
function appraisalTrace(memory) {
  if (!memory) return '<p class="field-note">برای دیدن علت واکنش، زمان را یک ساعت جلو ببر یا یک برخورد بساز.</p>';
  const before = memory.emotionsBefore, after = memory.emotionsAfter;
  return `<section class="appraisal-trace"><div class="section-label">چرا این واکنش را نشان داد؟</div><p class="trace-fact">اتفاق: ${esc(memory.text)}</p><p>برداشت: ${esc(memory.interpretation)}</p>${before && after ? `<div class="trace-deltas">${Object.keys(emotionLabels).map(key => {
    const delta = after[key] - before[key];
    return `<span>${emotionLabels[key]} <b dir="ltr">${tracePercent(before[key])} → ${tracePercent(after[key])}</b><small>${delta > .001 ? 'افزایش' : delta < -.001 ? 'کاهش' : 'تقریباً ثابت'}</small></span>`;
  }).join('')}</div>` : ''}<p class="trace-reason">واکنش: ${esc(memory.reactionReason ?? memory.publicText ?? 'ثبت نشده')}</p>${memory.masked ? '<span class="small-badge purple">احساس درونی با ظاهر یکسان نیست</span>' : ''}${memory.factors ? `<details><summary>جزئیات برداشت</summary>${memory.factors.map(f => meter(f.label,f.value,'teal')).join('')}</details>` : ''}</section>`;
}
export function renderMetrics(world) {
  const m = world._viewMetrics ?? metrics(world);
  const cards = [
    { label: 'زندگی‌های مستقل', value: number(world.agents.length), suffix: 'نفر', sub: `${number(m.connections)} پیوند آشنا`, icon: 'people', key: null, color: '#83bbbd' },
    { label: 'حال عمومی جامعه', value: number(m.wellbeing * 100), suffix: 'از ۱۰۰', sub: 'ترکیبی از نیازها و احساسات', icon: 'heart', key: 'wellbeing', color: '#c9ed8c' },
    { label: 'اعتماد در رابطه‌ها', value: number(m.trust * 100), suffix: 'از ۱۰۰', sub: 'میانگین اعتماد جهت‌دار', icon: 'link', key: 'trust', color: '#83bbbd' },
    { label: 'فاصلهٔ درون و ظاهر', value: number(m.gap * 100), suffix: 'از ۱۰۰', sub: 'تفاوت گرمی ظاهر با حال درونی', icon: 'eye', key: 'gap', color: '#b89af4' },
  ];
  return cards.map(card => `<article class="metric-card"><div class="metric-label">${esc(card.label)}<span class="metric-icon">${icon(card.icon, 17)}</span></div><div class="metric-value">${card.value}<span>${card.suffix}</span></div><div class="metric-bottom"><span>${esc(card.sub)}</span>${card.key ? sparkline(world.history.slice(-36).map(h => h[card.key]), card.color) : '<span class="population-dots"><i></i><i></i><i></i><i></i><i></i></span>'}</div></article>`).join('') + (world.schemaVersion === 2 ? `<div class="society-emotions"><span>میانگین احساس جامعه</span>${feelingsRow(Object.fromEntries(Object.keys(emotionLabels).map(key => [key,m[key]])))}</div>` : '');
}
export function renderAgentHeader(agent) {
  const state = mood(agent);
  return `<div class="inspector-label"><span>یک زندگی از نزدیک</span><span class="mono">#${agent.id.split('-').at(-1).padStart(3, '0')}</span></div><div class="agent-profile"><div class="avatar large" style="--avatar-color:${state.color}">${initials(agent.identity.name)}</div><div><h2>${esc(agent.identity.name)}</h2><p>${number(agent.identity.age)} ساله <span>·</span> ${esc(agent.identity.role)}</p></div><span class="mood-dot" style="background:${state.color}" title="${state.label}"></span></div><div class="agent-micro-stats"><span>حال فرد <strong>${percent(wellbeing(agent))}</strong></span><span>خاطره‌ها <strong>${number(agent._view?.memoryCount ?? agent.memories.length)}</strong></span><span>آشنایان <strong>${number(Object.keys(agent.relationships).length)}</strong></span></div>`;
}

export function renderAgentDetail(world, agent, tab) {
  if (tab === 'identity') {
    return `<div class="detail-section"><div class="section-label">پیشینه</div><p class="body-copy">${esc(agent.identity.background)}</p><span class="source-note">پیشینهٔ اولیه، هنگام خلق جهان</span></div><div class="detail-section"><div class="section-label">چیزهایی که برایش مهم‌اند</div><div class="value-tags">${Object.entries(agent.values).sort((a,b) => b[1]-a[1]).map(([key,value]) => `<span>${valueLabels[key]} <b>${percent(value)}</b></span>`).join('')}</div></div><div class="detail-section"><div class="section-label">شخصیت</div>${Object.entries(agent.traits).map(([key,value]) => meter(traitLabels[key], value, 'teal')).join('')}</div><div class="detail-section"><div class="section-label">باور فعلی دربارهٔ جهان</div>${Object.entries(agent.beliefs).map(([key,value]) => meter(beliefLabels[key], value, 'purple')).join('')}</div><div class="detail-section"><div class="section-label">افق زندگی</div><p class="body-copy">${esc(agent.goals.longTerm)}</p></div>`;
  }
  if (tab === 'memories') {
    return `<div class="detail-section"><div class="section-label">زندگی از نگاه خودش <span>${number(agent._view?.memoryCount ?? agent.memories.length)} خاطره</span></div><p class="field-note">واقعیت رویداد و برداشت شخصی، جدا ثبت شده‌اند.</p></div><div class="memory-list">${[...agent.memories].reverse().slice(0, 24).map(m => `<article class="memory-item"><div class="memory-top"><span class="${m.masked ? 'purple-text' : ''}">${m.source === 'background' ? 'پیشینهٔ اولیه' : m.kind === 'appraisal' ? 'برداشت شخصی' : kindLabels[m.kind] ?? 'مرور تجربه'}</span><time>${m.source === 'background' ? 'پیش از شروع' : dayTime(m.tick)}</time></div><p>${esc(m.text)}</p><blockquote>${esc(m.interpretation)}</blockquote>${m.feelings ? `<div class="memory-feelings">${feelingsRow(m.feelings)}</div>` : ''}${m.publicText ? `<div class="memory-expression">در ظاهر: «${esc(m.publicText)}»</div>` : ''}${m.reactionReason ? `<p class="field-note">${esc(m.reactionReason)}</p>` : ''}${m.masked ? '<span class="small-badge purple">احساس پیچیده، ظاهر گرم</span>' : ''}</article>`).join('')}</div>`;
  }
  if (tab === 'relations') {
    const relations = Object.entries(agent.relationships).sort((a,b) => b[1].familiarity-a[1].familiarity);
    return `<div class="detail-section"><div class="section-label">رابطه‌ها از نگاه ${esc(agent.identity.name.split(' ')[0])}</div><p class="field-note">این احساس‌ها متعلق به همین فردند؛ طرف مقابل ممکن است برداشت دیگری داشته باشد.</p></div><div class="relationship-list">${relations.length ? relations.map(([id,r]) => {
      const other = world.agents.find(a => a.id === id);
      if (!other) return '';
      return `<button class="relation-card" data-agent="${esc(id)}"><div class="relation-name"><span class="avatar small" style="--avatar-color:${mood(other).color}">${initials(other.identity.name)}</span><strong>${esc(other.identity.name)}</strong>${icon('arrow', 14)}</div><div class="relation-values"><span>اعتماد <b>${percent(r.trust)}</b></span><span>محبت <b>${percent(r.affection)}</b></span><span>دلخوری <b>${percent(r.resentment)}</b></span></div></button>`;
    }).join('') : '<p class="empty-state">هنوز رابطه‌ای شکل نگرفته است.</p>'}</div>`;
  }
  const appraisal = agent.memories.find(m => m.id === agent.extensions?.emotionModel?.memoryId) ?? agent.memories.findLast(m => m.kind === 'appraisal');
  const decision = agent.lastDecision;
  const sortedFactors = decision?.factors.filter(f => Math.abs(f.value) > .015).sort((a,b) => Math.abs(b.value)-Math.abs(a.value)).slice(0, 4) ?? [];
  return `<div class="detail-section public-section"><div class="section-label">${icon('eye', 14)} واکنش بیرونی <span class="small-badge">${actionLabels[agent.publicState.action] ?? 'در حال زندگی'}</span></div><blockquote class="public-quote">«${esc(agent.publicState.text)}»</blockquote></div><div class="detail-section"><div class="section-label">${icon('heart', 14)} پنج احساس فعلی</div>${Object.entries(agent.emotions).map(([key,value]) => meter(emotionName(key), value, key === 'disgust' ? 'purple' : key === 'fear' || key === 'anxiety' || key === 'anger' ? 'amber' : 'green')).join('')}</div>${appraisalTrace(appraisal)}<details class="detail-section"><summary>نیازها و انتخاب فعالیت</summary><div class="section-label">آخرین فعالیت <span>${decision ? actionLabels[decision.actionId] : 'هنوز انتخابی نشده'}</span></div>${sortedFactors.map(f => `<div class="factor-row"><span>${esc(f.label)}</span><div class="factor-track"><i style="width:${Math.min(100, Math.abs(f.value)*100)}%"></i></div></div>`).join('')}${Object.entries({ energy:'انرژی', belonging:'تعلق', safety:'امنیت', esteem:'حس توانمندی' }).map(([key,label]) => meter(label,agent.needs[key],agent.needs[key]<.3?'amber':'teal')).join('')}</details><div class="goal-note">${icon('spark',15)}<span>${esc(agent.goals.immediate)}</span></div>`;
}

export function renderFeed(world, filter, selectedId) {
  const events = [...world.events].reverse().filter(e => filter === 'all' || filter === 'selected' && (e.actorId === selectedId || e.targetId === selectedId || e.observers.includes(selectedId)) || filter === 'social' && !['rest','reflection','intervention','living_conditions'].includes(e.kind)).slice(0, 30);
  return events.length ? events.map(e => `<button class="event-row" data-event="${esc(e.id)}"><span class="event-icon ${e.kind === 'conflict' || e.kind === 'rejection' ? 'amber' : e.kind === 'achievement' ? 'purple' : ''}">${icon(e.kind === 'achievement' ? 'spark' : e.kind === 'help' ? 'heart' : e.kind === 'intervention' ? 'sliders' : 'link',16)}</span><span class="event-body"><span>${esc(e.text)}</span><small>${esc(kindLabels[e.kind] ?? 'رویداد')} ${e.origin === 'observer' ? '· ساختهٔ ناظر' : ''}</small></span><time>${number((8+e.tick)%24).padStart(2,'۰')}:۰۰<span>روز ${number(Math.floor((8+e.tick)/24)+1)}</span></time></button>`).join('') : '<div class="empty-state">هنوز رویدادی در این بخش ثبت نشده. زمان را یک گام جلو ببر.</div>';
}

export function renderPeople(world, query = '') {
  const people = world.agents.filter(a => `${a.identity.name} ${a.identity.role}`.includes(query.trim()));
  return people.length ? people.map(a => {
    const state = mood(a);
    const strongest = Object.entries(a.values).sort((x,y) => y[1]-x[1])[0][0];
    return `<button class="person-card" data-agent="${a.id}"><div class="person-card-top"><span class="avatar" style="--avatar-color:${state.color}">${initials(a.identity.name)}</span><span class="small-badge ${state.className}">${state.label}</span></div><h3>${esc(a.identity.name)}</h3><p>${number(a.identity.age)} ساله · ${esc(a.identity.role)}</p><div class="person-value">${valueLabels[strongest]} برایش مهم است</div><span class="person-action">${esc(actionLabels[a.publicState.action] ?? 'در حال زندگی')} ${icon('arrow',14)}</span></button>`;
  }).join('') : '<p class="empty-state">فردی با این مشخصات پیدا نشد.</p>';
}

export function renderConditions(world) {
  const labels = { abundance: ['فراوانی امکانات', 'کمبود امکانات ← بازیابی کمتر انرژی و تجربهٔ ناکامی'], socialSafety: ['امنیت اجتماعی', 'ناامنی ← تهدید برداشت‌شده؛ ترس بسته به حساسیت و توان فرد'], pressure: ['فشار محیط', 'فشار بیشتر ← خستگی و کاهش توان کنار آمدن با موقعیت'] };
  return Object.entries(labels).map(([key,[label,hint]]) => `<label class="condition-control"><span>${label}<strong data-condition-value="${key}">${percent(world.settings[key])}</strong></span><input type="range" min="0" max="100" value="${Math.round(world.settings[key]*100)}" data-condition="${key}" aria-label="${label}"><small>${hint}</small></label>`).join('');
}

export function renderExperiment(world, eventId) {
  if (!eventId) return '';
  const event = world.events.find(e => e.id === eventId);
  if (!event) return '<div class="notice">این آزمایش از پنجرهٔ رویدادهای اخیر خارج شده است. آزمایش تازه‌ای اجرا کن.</div>';
  const rows = event.observers.map(id => ({ agent: world.agents.find(a => a.id === id), memory: world.agents.find(a => a.id === id)?.memories.findLast(m => m.eventId === event.id) })).filter(row => row.memory);
  return `<section class="panel result-panel"><div class="panel-heading"><div><h2>یک واقعیت، ${number(rows.length)} برداشت</h2><span>${esc(event.text)}</span></div><span class="small-badge purple">برای دیدن تغییر قبل و بعد، فرد را انتخاب کن</span></div><div class="reaction-grid">${rows.map(({agent,memory:m}) => `<button class="reaction-card" data-agent="${agent.id}"><div class="reaction-name"><span class="avatar small" style="--avatar-color:${mood(agent).color}">${initials(agent.identity.name)}</span><strong>${esc(agent.identity.name)}</strong></div><p>${esc(m.interpretation)}</p><p class="field-note">شدت احساس برانگیخته‌شده در این رویداد</p><div class="reaction-emotions">${feelingsRow(m.feelings)}</div><div class="reaction-public">در ظاهر: «${esc(m.publicText)}»</div><p class="field-note">${esc(m.reactionReason ?? '')}</p></button>`).join('')}</div></section>`;
}
