export const fa = new Intl.NumberFormat('fa-IR', { maximumFractionDigits: 0 });
export const number = n => fa.format(n);
export const percent = n => `${number(n * 100)}٪`;
export const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
export function clock(tick) { return `${number(Math.floor((8 + tick) / 24) + 1)} / ${number((8 + tick) % 24).padStart(2, '۰')}:۰۰`; }
export function dayTime(tick) { return `روز ${number(Math.floor((8 + tick) / 24) + 1)} · ساعت ${number((8 + tick) % 24).padStart(2, '۰')}:۰۰`; }
export const initials = name => name.split(' ').map(p => p[0]).slice(0, 2).join('');
export function mood(agent) {
  const e = agent.emotions;
  if (e.anxiety > .5 || e.anger > .4) return { label: 'تحت فشار', color: '#eaa36d', className: 'amber' };
  if (e.envy > .35) return { label: 'درگیر مقایسه', color: '#b89af4', className: 'purple' };
  if (e.joy > .42) return { label: 'خوشحال', color: '#c9ed8c', className: 'green' };
  if (e.sadness > .3) return { label: 'دلگیر', color: '#7bace0', className: 'blue' };
  return { label: 'آرام', color: '#83bbbd', className: 'teal' };
}
export const kindLabels = { achievement: 'پیشرفت', connection: 'گفت‌وگو', help: 'همراهی', conflict: 'اختلاف', rejection: 'دعوت ردشده', reconciliation: 'آشتی', reflection: 'تأمل', rest: 'استراحت', setback: 'تلاش', intervention: 'دخالت ناظر' };
