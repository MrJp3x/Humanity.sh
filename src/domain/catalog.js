export const traitLabels = {
  empathy: 'همدلی', ambition: 'بلندپروازی', sociability: 'معاشرت‌پذیری',
  sensitivity: 'حساسیت عاطفی', openness: 'پذیرش تجربه', patience: 'شکیبایی',
  selfControl: 'خویشتن‌داری', impressionManagement: 'مدیریت تصویر اجتماعی',
};
export const valueLabels = {
  care: 'مراقبت از دیگران', achievement: 'پیشرفت', fairness: 'انصاف',
  autonomy: 'استقلال', belonging: 'تعلق', honesty: 'صداقت',
};
export const beliefLabels = { trust: 'اعتماد به دیگران', fairness: 'منصفانه بودن جهان', selfWorth: 'باور به توانایی خود' };
export const emotionLabels = { joy: 'شادی', anxiety: 'اضطراب', envy: 'حسادت', anger: 'خشم', sadness: 'اندوه' };
export const actionLabels = {
  rest: 'استراحت', connect: 'گفت‌وگو', help: 'کمک', create: 'خلق و یادگیری',
  reflect: 'خلوت و تأمل', confront: 'اعتراض', celebrate: 'تبریک گفتن',
  withdraw: 'کناره‌گیری', practice: 'تلاش بیشتر',
};
export const locations = [
  { id: 'home', name: 'خانه‌ها', x: .20, y: .28, width: .27, height: .34 },
  { id: 'garden', name: 'باغ مشترک', x: .72, y: .25, width: .32, height: .30 },
  { id: 'square', name: 'میدان گفت‌وگو', x: .40, y: .72, width: .32, height: .30 },
  { id: 'studio', name: 'خانهٔ خلاقیت', x: .79, y: .73, width: .24, height: .28 },
];
export const actionLocations = {
  rest: 'home', reflect: 'garden', withdraw: 'home', connect: 'square',
  help: 'garden', create: 'studio', confront: 'square', celebrate: 'square', practice: 'studio',
};
export const firstNames = ['نازنین', 'آرمان', 'سارا', 'نیما', 'رها', 'کاوه', 'لیلا', 'سامان', 'مینا', 'آرش', 'مهسا', 'نوید', 'یاسمن', 'پارسا', 'نورا', 'کیان', 'هستی', 'امیر', 'ترانه', 'شایان', 'آوا', 'دانیال', 'نگار', 'بردیا', 'رویا', 'مانی', 'دریا', 'ماهان', 'پریسا', 'پویا', 'سپیده', 'سینا', 'غزل', 'رامین', 'بهار', 'اشکان', 'یلدا', 'حامی', 'آتوسا', 'ایلیا'];
export const lastNames = ['مهر', 'راد', 'آزاد', 'روشن', 'امید', 'نیک', 'پارسا', 'کیانی', 'صادقی', 'نادری', 'رضایی', 'بهرامی'];
export const roles = ['داستان‌نویس', 'باغبان', 'موسیقی‌دوست', 'آموزگار', 'پژوهشگر', 'هنرمند', 'سازنده', 'کتاب‌دوست'];
export const backgrounds = [
  { story: 'در جمعی حمایتگر بزرگ شده و برای دوستی‌های ماندگار ارزش قائل است.', trust: .16, fairness: .09, memory: 'وقتی در کارم شکست خوردم، دوستی کنارم ماند.' },
  { story: 'چند بار با قضاوت ناعادلانه روبه‌رو شده و به فرصت‌های برابر حساس است.', trust: -.12, fairness: -.19, memory: 'یک بار بدون شنیدن حرفم، دربارهٔ من تصمیم گرفتند.' },
  { story: 'با تلاش فردی به هدف‌هایش رسیده و استقلال برایش مهم است.', trust: -.02, fairness: .02, memory: 'با تمرین طولانی، کاری را که ناممکن می‌دانستم یاد گرفتم.' },
  { story: 'تجربهٔ جابه‌جایی و شروع دوباره دارد؛ هنوز در جست‌وجوی حس تعلق است.', trust: -.06, fairness: -.03, memory: 'در جمع تازه، کسی مرا به گفت‌وگو دعوت کرد.' },
  { story: 'در محیطی رقابتی رشد کرده و اغلب خودش را با دیگران مقایسه می‌کند.', trust: -.05, fairness: -.07, memory: 'روزی که موفق شدم، بیشتر از همیشه دیده شدم.' },
  { story: 'با تجربه‌های متنوع و آدم‌های متفاوت آشنا شده و به تغییر علاقه دارد.', trust: .05, fairness: .03, memory: 'آشنایی با یک دوست، نظرم را دربارهٔ یک موضوع عوض کرد.' },
];
