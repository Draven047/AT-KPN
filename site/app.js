const LANGS = {
  English: { tag: 'en', native: 'English', word: 'Hello', greeting: 'Hello, world.', sentence: 'How are you? Thank you.', letters: 'Aa Bb Cc Dd Ee Ff Gg Hh Ii Jj Kk Ll Mm Nn Oo Pp Qq Rr Ss Tt Uu Vv Ww Xx Yy Zz 0123456789' },
  Kannada: { tag: 'kn', native: 'ಕನ್ನಡ', word: 'ನಮಸ್ಕಾರ', sentence: 'ನೀವು ಹೇಗಿದ್ದೀರಿ? ಧನ್ಯವಾದಗಳು.', letters: 'ಕ ಕಾ ಕಿ ಕೀ ಕು ಕೂ ಕೃ ಕೆ ಕೇ ಕೈ ಕೊ ಕೋ ಕೌ ಕಂ ಕಃ ಕ್ಷ ಜ್ಞ ಶ್ರೀ ಕ್ಕ ಕ್ರ ರ್ಕ' },
  Hindi: { tag: 'hi', native: 'हिन्दी', word: 'नमस्ते', sentence: 'आप कैसे हैं? धन्यवाद।', letters: 'क का कि की कु कू कृ के कै को कौ कं कः क्ष त्र ज्ञ श्र क्र र्क फ़ ज़ ड़ ढ़' },
  Marathi: { tag: 'mr', native: 'मराठी', word: 'नमस्कार', sentence: 'तुम्ही कसे आहात? धन्यवाद.', letters: 'ळ ऱ ॲ ऑ ळा ळी ळू ऱ्ह र्‍य क्ष त्र ज्ञ श्री महाराष्ट्र मराठी' },
  Malayalam: { tag: 'ml', native: 'മലയാളം', word: 'നമസ്കാരം', sentence: 'സുഖമാണോ? നന്ദി.', letters: 'ക കാ കി കീ കു കൂ കൃ കെ കേ കൈ കൊ കോ കൗ ക്ക ക്ഷ ന്ത ൺ ൻ ർ ൽ ൾ ൿ' },
  Tamil: { tag: 'ta', native: 'தமிழ்', word: 'வணக்கம்', sentence: 'நீங்கள் எப்படி இருக்கிறீர்கள்? நன்றி.', letters: 'க கா கி கீ கு கூ கெ கே கை கொ கோ கௌ க் ங் ஞ் ண் ன் ற் ழ் ஸ்ரீ க்ஷ' },
  Telugu: { tag: 'te', native: 'తెలుగు', word: 'నమస్కారం', sentence: 'మీరు ఎలా ఉన్నారు? ధన్యవాదాలు.', letters: 'క కా కి కీ కు కూ కృ కె కే కై కొ కో కౌ కం కః క్క క్ర ర్క క్ష జ్ఞ శ్రీ' },
  Bengali: { tag: 'bn', native: 'বাংলা', word: 'নমস্কার', sentence: 'আপনি কেমন আছেন? ধন্যবাদ।', letters: 'ক কা কি কী কু কূ কৃ কে কৈ কো কৌ কং কঃ ক্ষ জ্ঞ ত্র শ্র ক্র র্ক ড় ঢ় য়' },
};
const ORDER = Object.keys(LANGS);
const WEIGHTS = { Light: 300, Regular: 400, Bold: 700 };
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
const motionOK = !reduceMotion.matches;
const finePointer = matchMedia('(hover: hover) and (pointer: fine)').matches;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const easeOut = t => 1 - (1 - t) ** 3;
const easeInOut = t => (t < .5 ? 4 * t * t * t : 1 - ((-2 * t + 2) ** 3) / 2);
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const baselineProbe = document.createElement('div');
baselineProbe.setAttribute('aria-hidden', 'true');
baselineProbe.style.cssText = 'position:absolute;left:-9999px;top:0;visibility:hidden;white-space:nowrap;font-family:AT-KPN,sans-serif;';
baselineProbe.innerHTML = 'H<span style="display:inline-block;width:0;height:0;vertical-align:baseline"></span>';
document.body.append(baselineProbe);

/** Distance (px) from the top of a line box to its baseline, measured from real layout. */
function baselineOffset(weight, size, lineHeight) {
  baselineProbe.style.fontWeight = weight;
  baselineProbe.style.fontSize = `${size}px`;
  baselineProbe.style.lineHeight = `${lineHeight}px`;
  return baselineProbe.lastElementChild.offsetTop;
}

/* ---------------- Header menu (small screens) ---------------- */
const menuButton = $('#menu-button');
const nav = $('#primary-nav');
function setMenu(open) {
  if (open) nav.dataset.open = ''; else delete nav.dataset.open;
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
}
menuButton.addEventListener('click', () => setMenu(!nav.hasAttribute('data-open')));
nav.addEventListener('click', event => { if (event.target.closest('a')) setMenu(false); });
addEventListener('keydown', event => { if (event.key === 'Escape' && nav.hasAttribute('data-open')) { setMenu(false); menuButton.focus(); } });

/* ---------------- A word built from characters ---------------- */
const ACCENT = '#f7e100';
const MONO_STACK = 'ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace';
const MONO_CHARS = '#$%&*+=?@0123456789ABCDEFGHKMNOPQRSTUVWXYZabcdeghkmnopqrsuvwxyz:;<>[]{}/';
/**
 * Sets a word very large out of small flickering characters on a canvas.
 * When the word changes, the characters first loosen and drift like dust, then travel
 * slowly along curved paths, left to right, into the new word. A band of light sweeps
 * through now and then, and the characters step aside from the pointer.
 */
class AsciiField {
  constructor(canvas, host, options = {}) {
    this.canvas = canvas; this.host = host; this.ctx = canvas.getContext('2d');
    this.options = { fitW: .86, fitH: .5, smallFitW: .92, cap: 1900, smallCap: 950, dust: 150, smallDust: 60, ...options };
    this.parts = []; this.dust = []; this.text = ''; this.lang = 'English'; this.script = [];
    this.pointer = { x: -1e4, y: -1e4, on: false };
    this.running = false; this.visible = false; this.ready = false; this.last = 0; this.t = 0;
    this.sampler = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
    this.resize();
    host.addEventListener('pointermove', event => {
      const box = canvas.getBoundingClientRect();
      this.pointer = { x: event.clientX - box.left, y: event.clientY - box.top, on: true };
    });
    host.addEventListener('pointerleave', () => { this.pointer.on = false; });
    addEventListener('resize', () => this.resize());
    document.addEventListener('visibilitychange', () => this.sync());
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(([entry]) => { this.visible = entry.isIntersecting; this.sync(); this.onVisible?.(this.visible); }).observe(canvas);
    } else { this.visible = true; }
  }
  sync() { if (this.visible && this.ready && !document.hidden) this.start(); else this.stop(); }
  resize() {
    const box = this.canvas.getBoundingClientRect();
    if (Math.abs(box.width - (this.w || 0)) < 2 && Math.abs(box.height - (this.h || 0)) < 2) return;
    this.dpr = Math.min(1.75, devicePixelRatio || 1);
    this.w = box.width; this.h = box.height; this.small = this.w < 700;
    this.canvas.width = Math.round(this.w * this.dpr); this.canvas.height = Math.round(this.h * this.dpr);
    this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    this.dust = Array.from({ length: this.small ? this.options.smallDust : this.options.dust }, () => ({
      x: Math.random() * this.w, y: Math.random() * this.h, z: Math.random(), r: .5 + Math.random() * 1.2,
      ph: Math.random() * 6.28, sp: .4 + Math.random() * 1.2, vx: (Math.random() - .5) * 3, vy: -(1 + Math.random() * 3),
    }));
    if (this.text) this.setText(this.text, this.lang, true);
    else if (!this.running) this.draw();
  }
  pick() {
    return this.script.length && Math.random() < .22
      ? { ch: this.script[Math.random() * this.script.length | 0], s: 1 }
      : { ch: MONO_CHARS[Math.random() * MONO_CHARS.length | 0], s: 0 };
  }
  /** Points inside the word when it is set large in the middle of the canvas. */
  sample(text) {
    const w = Math.max(1, Math.ceil(this.w)), h = Math.max(1, Math.ceil(this.h)), ctx = this.sampler, o = this.options;
    ctx.canvas.width = w; ctx.canvas.height = h;
    ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    ctx.font = '700 100px AT-KPN';
    const m = ctx.measureText(text);
    const width = (m.actualBoundingBoxLeft + m.actualBoundingBoxRight) || m.width || 1;
    const tall = (m.actualBoundingBoxAscent || 70) + (m.actualBoundingBoxDescent || 20);
    const size = Math.min(100 * w * (this.small ? o.smallFitW : o.fitW) / width, 100 * h * o.fitH / tall);
    ctx.font = `700 ${size}px AT-KPN`;
    const m2 = ctx.measureText(text);
    const up = m2.actualBoundingBoxAscent || size * .7, down = m2.actualBoundingBoxDescent || size * .2;
    const baseline = h / 2 + (up - down) / 2;
    const cx = w / 2 + ((m2.actualBoundingBoxLeft || 0) - (m2.actualBoundingBoxRight || 0)) / 2;
    ctx.fillStyle = '#fff'; ctx.fillText(text, cx, baseline);
    const data = ctx.getImageData(0, 0, w, h).data;
    let ink = 0;
    for (let i = 3; i < data.length; i += 16) if (data[i] > 140) ink += 4;
    const cap = this.small ? o.smallCap : o.cap;
    const step = clamp(Math.sqrt(ink / cap), this.small ? 4 : 6, 16);
    const pts = [];
    for (let y = 0, row = 0; y < h; y += step, row++) {
      for (let x = row % 2 ? step / 2 : 0; x < w; x += step) {
        if (data[((y | 0) * w + (x | 0)) * 4 + 3] > 140) pts.push([x + (Math.random() - .5) * 1.6, y + (Math.random() - .5) * 1.6]);
      }
    }
    for (let i = pts.length - 1; i > 0; i--) { const j = Math.random() * (i + 1) | 0; [pts[i], pts[j]] = [pts[j], pts[i]]; }
    return pts.slice(0, cap);
  }
  setText(text, lang = this.lang, instant = false) {
    this.text = text; this.lang = lang;
    this.script = lang === 'English' ? [] : LANGS[lang].letters.split(/\s+/).filter(t => [...t].length <= 3);
    if (!this.w) return;
    const pts = this.sample(text), now = performance.now();
    const alive = this.parts.filter(p => !p.dying), fading = this.parts.filter(p => p.dying), next = [];
    let minX = Infinity, maxX = -Infinity;
    for (const [x] of pts) { if (x < minX) minX = x; if (x > maxX) maxX = x; }
    const span = Math.max(1, maxX - minX);
    pts.forEach(([x, y], i) => {
      let p = alive[i];
      if (p) {
        // loosen: drift a little, mostly upward, before travelling
        const angle = Math.random() * 6.28, reach = 30 + Math.random() * 120;
        p.sx = p.bx; p.sy = p.by; p.a0 = p.a;
        p.mx = p.bx + Math.cos(angle) * reach; p.my = p.by + Math.sin(angle) * reach * .7 - 20 - Math.random() * 50;
      } else {
        const sx = x + (Math.random() - .5) * this.w * .5, sy = y + (Math.random() - .5) * this.h * .7;
        p = { bx: sx, by: sy, sx, sy, mx: sx + (Math.random() - .5) * 40, my: sy - Math.random() * 40, a: 0, a0: 0, ox: 0, oy: 0, vox: 0, voy: 0, glow: 0 };
      }
      Object.assign(p, this.pick(), {
        tx: x, ty: y, dying: false, settled: false,
        tA: now + Math.random() * 300,
        tB: now + 1500 + ((x - minX) / span) * 1300 + Math.random() * 420,
        dB: 2300 + Math.random() * 900,
        curve: (Math.random() - .5) * 90, base: .3 + Math.random() * .62, seed: Math.random() * 100,
      });
      if (instant || !motionOK) { p.bx = p.sx = p.mx = x; p.by = p.sy = p.my = y; p.a = p.base; p.tB = now - 1e5; p.settled = true; }
      next.push(p);
    });
    for (const p of alive.slice(pts.length)) {
      const angle = Math.random() * 6.28, reach = 60 + Math.random() * 160;
      Object.assign(p, { dying: true, sx: p.bx, sy: p.by, a0: p.a, mx: p.bx + Math.cos(angle) * reach, my: p.by + Math.sin(angle) * reach * .7 - 40, tA: now + Math.random() * 400, dB: 1900 + Math.random() * 900 });
      next.push(p);
    }
    this.parts = (instant || !motionOK) ? next.filter(p => !p.dying) : next.concat(fading);
    if (!this.running) this.draw();
  }
  start() {
    if (this.running || !motionOK) return;
    this.running = true; this.last = performance.now();
    const loop = now => {
      if (!this.running) return;
      const dt = Math.min(.05, (now - this.last) / 1000); this.last = now;
      this.step(dt, now); this.draw();
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }
  stop() { this.running = false; }
  step(dt, now) {
    this.t += dt;
    const { x: px, y: py, on } = this.pointer;
    const sweep = ((this.t * .06) % 1.7 - .35) * this.w;
    const reachR = this.small ? 70 : 130;
    for (const p of this.parts) {
      if (p.dying) {
        const u = clamp((now - p.tA) / p.dB, 0, 1), e = easeOut(u);
        p.bx = p.sx + (p.mx - p.sx) * e; p.by = p.sy + (p.my - p.sy) * e; p.a = p.a0 * (1 - u);
        if (u >= 1) p.dead = true;
        continue;
      }
      if (now < p.tB) {                                    // loosening
        const u = clamp((now - p.tA) / Math.max(1, p.tB - p.tA), 0, 1), e = easeOut(u);
        p.bx = p.sx + (p.mx - p.sx) * e; p.by = p.sy + (p.my - p.sy) * e;
        p.a = p.a0 + (p.base * .3 - p.a0) * u;
      } else if (!p.settled) {                             // travelling, on a curved path
        const u = clamp((now - p.tB) / p.dB, 0, 1), e = easeInOut(u), arc = Math.sin(Math.PI * u) * p.curve;
        const dx = p.tx - p.mx, dy = p.ty - p.my, len = Math.hypot(dx, dy) || 1;
        p.bx = p.mx + dx * e - dy / len * arc; p.by = p.my + dy * e + dx / len * arc;
        p.a = p.base * (.3 + .7 * e);
        if (u >= 1) p.settled = true;
      } else {                                             // resting, with a breath of movement
        p.bx = p.tx + Math.sin(this.t * .9 + p.seed) * 1.1; p.by = p.ty + Math.cos(this.t * .8 + p.seed) * 1.1;
        p.a = p.base;
      }
      let hot = 0;
      if (on) {
        const dx = p.bx + p.ox - px, dy = p.by + p.oy - py, d = Math.hypot(dx, dy);
        if (d < reachR && d > .1) { hot = 1 - d / reachR; p.vox += dx / d * hot * 1700 * dt; p.voy += dy / d * hot * 1700 * dt; }
      }
      p.vox += (-p.ox * 34 - p.vox * 7) * dt; p.voy += (-p.oy * 34 - p.voy * 7) * dt;
      p.ox += p.vox * dt; p.oy += p.voy * dt;
      const lit = p.settled ? Math.max(0, 1 - Math.abs(p.bx - sweep) / 140) : 0;
      p.glow += (Math.max(hot * .7, lit * .5) - p.glow) * Math.min(1, dt * 5);
      if (Math.random() < dt * (.7 + lit * 5)) Object.assign(p, this.pick());
    }
    this.parts = this.parts.filter(p => !p.dead);
    for (const d of this.dust) {
      d.x += d.vx * dt; d.y += d.vy * dt * (.4 + d.z);
      if (d.y < -4) { d.y = this.h + 4; d.x = Math.random() * this.w; }
      if (d.x < -4) d.x = this.w + 4; else if (d.x > this.w + 4) d.x = -4;
    }
  }
  draw() {
    const { ctx } = this;
    ctx.clearRect(0, 0, this.w, this.h);
    ctx.fillStyle = '#fff';
    for (const d of this.dust) {
      ctx.globalAlpha = (.08 + .4 * d.z) * (.55 + .45 * Math.sin(this.t * d.sp + d.ph));
      ctx.fillRect(d.x, d.y, d.r, d.r);
    }
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    for (const script of [0, 1]) {
      ctx.font = script ? `700 ${this.small ? 8 : 12}px AT-KPN` : `${this.small ? 7 : 11}px ${MONO_STACK}`;
      for (const p of this.parts) {
        if (p.s !== script) continue;
        const alpha = Math.min(1, Math.max(0, p.a) + p.glow);
        if (alpha < .02) continue;
        ctx.globalAlpha = alpha;
        ctx.fillStyle = p.glow > .14 ? ACCENT : '#fff';
        ctx.fillText(p.ch, p.bx + p.ox, p.by + p.oy);
      }
    }
    ctx.globalAlpha = 1;
  }
}

/* ---------------- Hero: the eight greetings, one slow change at a time ---------------- */
const heroSection = $('#hero');
const hero = { field: null, index: 0, playing: motionOK, visible: true, timer: null, play: $('#hero-play'), caption: $('#hero-caption') };
const CYCLE = 8900;           // about 5 s to change (last character lands at 6.4 s), about 2.5 s fully formed
function heroCaption(index) {
  const name = ORDER[index];
  const write = () => {
    $('#hero-count').textContent = `${String(index + 1).padStart(2, '0')} / ${String(ORDER.length).padStart(2, '0')}`;
    $('#hero-lang').textContent = name;
    delete hero.caption.dataset.changing;
  };
  if (!motionOK) { write(); return; }
  hero.caption.dataset.changing = '';
  setTimeout(write, 1500);
}
function showGreeting(index, instant = false) {
  hero.index = index;
  const name = ORDER[index];
  hero.field?.setText(LANGS[name].word, name, instant);
  heroCaption(index);
}
function scheduleHero() {
  clearTimeout(hero.timer);
  if (!hero.playing || !hero.visible || document.hidden) return;
  hero.timer = setTimeout(() => { showGreeting((hero.index + 1) % ORDER.length); scheduleHero(); }, CYCLE);
}
function setPlaying(playing) {
  hero.playing = playing;
  hero.play.setAttribute('aria-pressed', String(playing));
  hero.play.setAttribute('aria-label', playing ? 'Pause the animation' : 'Play the animation');
  scheduleHero();
}
hero.play.addEventListener('click', () => setPlaying(!hero.playing));
if (!hero.playing) setPlaying(false);
if ($('#hero-field').getContext) {
  hero.field = new AsciiField($('#hero-field'), heroSection);
  hero.field.onVisible = visible => { hero.visible = visible; scheduleHero(); };
}
document.addEventListener('visibilitychange', scheduleHero);

/* ---------------- Closing panel: the name, built the same way ---------------- */
let ctaField = null;
if ($('#cta-field').getContext) {
  ctaField = new AsciiField($('#cta-field'), $('#cta-panel'), { fitW: .8, smallFitW: .9, fitH: .52, cap: 1300, smallCap: 700, dust: 50, smallDust: 24 });
  ctaField.onVisible = visible => { if (visible && ctaField.ready && !ctaField.text) ctaField.setText('AT-KPN', 'English'); };
}

/* ---------------- Language index: weights on hover, open in the tester ---------------- */
$$('.lang-row').forEach(row => {
  const greet = $('.lang-greet', row);
  const label = $('.voice-weight', row);
  const sequence = ['Light', 'Regular', 'Bold'];
  let timer = null; let step = 0;
  const show = weight => { greet.style.fontWeight = WEIGHTS[weight]; label.textContent = `${weight} ${WEIGHTS[weight]}`; };
  const start = () => {
    if (!motionOK || timer) return;
    step = 0; show(sequence[0]);
    timer = setInterval(() => { step = (step + 1) % 3; show(sequence[step]); }, 700);
  };
  const stop = () => { clearInterval(timer); timer = null; show('Bold'); };
  row.addEventListener('pointerenter', start);
  row.addEventListener('pointerleave', stop);
  row.addEventListener('focus', start);
  row.addEventListener('blur', stop);
});
$$('[data-try]').forEach(link => link.addEventListener('click', event => {
  event.preventDefault();
  openInTester(link.dataset.try);
}));

/* ---------------- Tester ---------------- */
const state = { language: 'English', weight: 'Bold', format: 'TTF', theme: 'black', preset: 'greeting', texts: new Map() };
const descriptions = { TTF: 'TrueType · for desktop apps', OTF: 'OpenType CFF · for desktop apps', WOFF2: 'WOFF2 · compact web fonts', WOFF: 'WOFF · web font fallback' };
const preview = $('#preview-text');
const size = $('#font-size');
const studio = $('.type-studio');
const currentDownload = $('#current-download');
let catalog;

function presetText(language = state.language) {
  const info = LANGS[language];
  return state.preset === 'greeting' ? (info.greeting || info.word) : info[state.preset];
}
function resizePreview() {
  preview.style.height = 'auto';
  preview.style.height = `${Math.min(660, Math.max(innerWidth <= 640 ? 170 : 220, preview.scrollHeight))}px`;
}
function updateDownload() {
  const row = catalog?.languages.find(item => item.id === state.language);
  if (row) currentDownload.href = row.fonts[state.weight][state.format].path;
  currentDownload.textContent = `Download ${state.language} ${state.weight} · ${state.format}`;
}
function updateProofs() {
  const sample = preview.value || presetText();
  $$('[data-proof-weight]').forEach(proof => {
    proof.textContent = sample;
    proof.lang = LANGS[state.language].tag;
    proof.style.fontFeatureSettings = preview.style.fontFeatureSettings;
  });
}
function updatePreview() {
  preview.lang = LANGS[state.language].tag;
  preview.style.fontWeight = WEIGHTS[state.weight];
  preview.style.fontFeatureSettings = state.language === 'Malayalam' && $('#stacked-form').checked ? '"ss01" 1' : '"ss01" 0';
  $('#preview-caption').textContent = `AT-KPN ${state.language} · ${state.weight} ${WEIGHTS[state.weight]}`;
  $('#malayalam-option').hidden = state.language !== 'Malayalam';
  updateProofs();
  updateDownload();
  resizePreview();
}
function selectLanguage(language) {
  if (!LANGS[language]) return;
  state.texts.set(state.language, preview.value);
  state.language = language;
  const saved = state.texts.get(language);
  preview.value = saved !== undefined && saved !== presetText(language) ? saved : presetText(language);
  $$('[data-lang]').forEach(item => item.setAttribute('aria-pressed', String(item.dataset.lang === language)));
  updatePreview();
}
function openInTester(language) {
  selectLanguage(language);
  $('#try').scrollIntoView({ behavior: motionOK ? 'smooth' : 'auto' });
  setTimeout(() => preview.focus({ preventScroll: true }), motionOK ? 650 : 0);
}
$$('[data-lang]').forEach(button => button.addEventListener('click', () => selectLanguage(button.dataset.lang)));
$$('[data-preset]').forEach(button => button.addEventListener('click', () => {
  state.preset = button.dataset.preset;
  $$('[data-preset]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  state.texts.clear();
  preview.value = presetText();
  updatePreview();
}));
$$('.weight-control [data-weight]').forEach(button => button.addEventListener('click', () => {
  state.weight = button.dataset.weight;
  $$('.weight-control [data-weight]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  updatePreview();
}));
$$('.color-control [data-theme]').forEach(button => button.addEventListener('click', () => {
  state.theme = button.dataset.theme;
  studio.dataset.theme = state.theme;
  $$('.color-control [data-theme]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
}));
function updateSize() {
  preview.style.fontSize = `${size.value}px`;
  $('#size-output').textContent = `${size.value} px`;
  resizePreview();
}
size.addEventListener('input', updateSize);
preview.addEventListener('input', () => { state.texts.set(state.language, preview.value); updateProofs(); resizePreview(); });
$('#stacked-form').addEventListener('change', updatePreview);
$('#reset-text').addEventListener('click', () => {
  preview.value = presetText();
  state.texts.delete(state.language);
  updatePreview();
});

/* ---------------- Character set ---------------- */
const glyphs = { data: null, script: null, pinned: null, weight: 'Bold', seen: false };
const inspector = { glyph: $('#inspector-glyph'), line: $('#inspector-line') };
function codePoint(ch) { return `U+${ch.codePointAt(0).toString(16).toUpperCase().padStart(4, '0')}`; }
function placeInspectorLine() {
  const style = getComputedStyle(inspector.glyph);
  const offset = baselineOffset(WEIGHTS[glyphs.weight], parseFloat(style.fontSize), parseFloat(style.lineHeight));
  inspector.line.style.top = `${Math.round(inspector.glyph.offsetTop + offset)}px`;
}
function inspect(cell) {
  if (!cell) return;
  const ch = cell.dataset.char;
  const tag = glyphs.script.tag;
  if (motionOK && inspector.glyph.textContent !== ch) {
    inspector.glyph.classList.remove('swap'); void inspector.glyph.offsetWidth; inspector.glyph.classList.add('swap');
  }
  inspector.glyph.textContent = ch; inspector.glyph.lang = tag;
  ['300', '400', '700'].forEach(w => { const s = $(`#iw-${w}`); s.textContent = ch; s.lang = tag; });
  $('#inspector-name').textContent = cell.dataset.name;
  $('#inspector-code').textContent = codePoint(ch);
  $('#inspector-group').textContent = cell.dataset.group;
  $('#copy-glyph').textContent = `Copy ${ch}`;
  placeInspectorLine();
}
function pin(cell) {
  if (glyphs.pinned) glyphs.pinned.setAttribute('aria-pressed', 'false');
  glyphs.pinned = cell;
  cell.setAttribute('aria-pressed', 'true');
  $('#copy-glyph-status').textContent = '';
  inspect(cell);
}
function showScript(id) {
  glyphs.script = glyphs.data.scripts.find(s => s.id === id);
  $$('#script-tabs button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.script === id)));
  const box = $('#glyph-groups');
  box.textContent = '';
  for (const group of glyphs.script.groups) {
    const section = document.createElement('div'); section.className = 'glyph-group';
    const title = document.createElement('h3'); title.textContent = group.name;
    const count = document.createElement('small'); count.textContent = `${group.chars.length}`; title.append(count);
    const grid = document.createElement('div'); grid.className = 'glyph-grid';
    for (const [ch, name] of group.chars) {
      const cell = document.createElement('button');
      cell.type = 'button'; cell.className = 'glyph-cell'; cell.lang = glyphs.script.tag;
      cell.textContent = ch; cell.dataset.char = ch; cell.dataset.name = name; cell.dataset.group = group.name;
      cell.setAttribute('aria-pressed', 'false');
      cell.setAttribute('aria-label', `${ch}, ${name.toLowerCase()}`);
      grid.append(cell);
    }
    section.append(title, grid); box.append(section);
  }
  if (glyphs.seen) cascadeCells();
  pin($('.glyph-cell', box));
}
/** Cells fall into place one after another (only once the section is on screen). */
function cascadeCells() {
  if (!motionOK) return;
  $$('#glyph-groups .glyph-cell').forEach((cell, i) => {
    cell.classList.remove('cell-in'); cell.style.setProperty('--cd', `${Math.min(i * 9, 520)}ms`);
    void cell.offsetWidth; cell.classList.add('cell-in');
  });
}
function initGlyphs(data) {
  glyphs.data = data;
  const tabs = $('#script-tabs');
  for (const script of data.scripts) {
    const button = document.createElement('button');
    button.type = 'button'; button.dataset.script = script.id; button.setAttribute('aria-pressed', 'false');
    const native = document.createElement('span'); native.lang = script.tag; native.textContent = script.sample;
    button.append(document.createTextNode(script.label), native);
    button.addEventListener('click', () => showScript(script.id));
    tabs.append(button);
  }
  const groupsBox = $('#glyph-groups');
  groupsBox.addEventListener('pointerover', event => { const cell = event.target.closest('.glyph-cell'); if (cell) inspect(cell); });
  groupsBox.addEventListener('pointerleave', () => inspect(glyphs.pinned));
  groupsBox.addEventListener('focusin', event => { const cell = event.target.closest('.glyph-cell'); if (cell) inspect(cell); });
  groupsBox.addEventListener('click', event => { const cell = event.target.closest('.glyph-cell'); if (cell) pin(cell); });
  showScript(data.scripts[0].id);
}
$$('[data-glyph-weight]').forEach(button => button.addEventListener('click', () => {
  glyphs.weight = button.dataset.glyphWeight;
  $$('[data-glyph-weight]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  inspector.glyph.style.fontWeight = WEIGHTS[glyphs.weight];
  $('#inspector-tag').textContent = `${glyphs.weight} ${WEIGHTS[glyphs.weight]}`;
  placeInspectorLine();
}));
$('#copy-glyph').addEventListener('click', async () => {
  const ch = glyphs.pinned?.dataset.char || inspector.glyph.textContent;
  const status = $('#copy-glyph-status');
  try { await navigator.clipboard.writeText(ch); status.textContent = `Copied ${ch}`; } catch { status.textContent = 'Select the letter to copy it.'; }
});
fetch('glyphs.json').then(response => {
  if (!response.ok) throw new Error('Glyph data unavailable');
  return response.json();
}).then(initGlyphs).catch(() => { $('#glyph-groups').innerHTML = '<p class="small-note">The character set could not load. Try the tester above.</p>'; });

/* ---------------- Downloads ---------------- */
$$('[data-format]').forEach(button => button.addEventListener('click', () => {
  if (!catalog) return;
  state.format = button.dataset.format;
  $$('[data-format]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  $('#format-description').textContent = descriptions[state.format];
  $$('.download-row').forEach(row => {
    const language = catalog.languages.find(item => item.id === row.dataset.language);
    $$('.weight-download', row).forEach(link => {
      link.href = language.fonts[link.dataset.weight][state.format].path;
      link.setAttribute('aria-label', `Download ${language.name} ${link.dataset.weight} ${state.format}`);
      link.querySelector('span').textContent = state.format;
    });
  });
  updateDownload();
}));
$('#copy-css').addEventListener('click', async () => {
  const status = $('#copy-status');
  try { await navigator.clipboard.writeText($('#web-code').textContent); status.textContent = 'Code copied.'; } catch { status.textContent = 'Select the code above and copy it manually.'; }
});

/* ---------------- Motion: statement, counters, headings, reveals, magnetic buttons, scroll ---------------- */
// The intro statement lights up word by word as it is scrolled through.
const statement = $('#statement');
const statementWords = statement.textContent.trim().split(/\s+/).map((word, i, all) => {
  const span = document.createElement('span'); span.className = motionOK ? 'fw' : 'fw on'; span.textContent = word;
  if (i === 0) statement.textContent = '';
  statement.append(span, i < all.length - 1 ? ' ' : '');
  return span;
});
let litWords = motionOK ? 0 : statementWords.length;

// The numbers count up the first time they are seen.
function countUp(el) {
  const target = Number(el.dataset.count), start = performance.now(), duration = 1300 + Math.min(900, target / 4);
  const tick = now => {
    const u = clamp((now - start) / duration, 0, 1);
    el.textContent = Math.round(target * easeOut(u)).toLocaleString('en-US');
    if (u < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

/** Wrap each word of a heading so it can rise out of its own mask. */
function splitWords(el) {
  const words = el.textContent.trim().split(/\s+/);
  el.setAttribute('aria-label', el.textContent.trim());
  el.textContent = '';
  words.forEach((word, i) => {
    const outer = document.createElement('span'); outer.className = 'w'; outer.setAttribute('aria-hidden', 'true');
    const inner = document.createElement('span'); inner.textContent = word; inner.style.setProperty('--wi', i);
    outer.append(inner); el.append(outer);
    if (i < words.length - 1) el.append(' ');
  });
  el.dataset.split = '';
}
const revealObserver = 'IntersectionObserver' in window ? new IntersectionObserver(entries => entries.forEach(entry => {
  if (!entry.isIntersecting) return;
  const el = entry.target;
  el.dataset.shown = '';
  revealObserver.unobserve(el);
  // once in place, drop the stagger delay so hover effects answer at once
  setTimeout(() => { el.dataset.done = ''; }, 1700 + (parseFloat(el.style.getPropertyValue('--delay')) || 0));
  if (el.id === 'stats') $$('[data-count]', el).forEach(countUp);
  // a fully clipped element never counts as visible, so wipes are started by their container
  if (el.classList.contains('weights')) $$('.weight-col', el).forEach(col => { col.dataset.shown = ''; setTimeout(() => { col.dataset.done = ''; }, 2200); });
  if (el.classList.contains('glyph-layout') && !glyphs.seen) { glyphs.seen = true; cascadeCells(); }
}), { rootMargin: '0px 0px -8% 0px', threshold: .08 }) : null;

if (motionOK && revealObserver) {
  $$('.section-head h2, .cta-copy h2').forEach(h => { splitWords(h); revealObserver.observe(h); });
  revealObserver.observe($('#stats'));
  const plan = [['.eyebrow', 'up'], ['.section-head > p', 'up'], ['.stats > div', 'up', 90], ['.intro-actions', 'up'], ['.lang-row', 'up', 55],
    ['.language-tabs', 'up'], ['.type-studio', 'up'], ['.weight-col', 'wipe', 140], ['#script-tabs', 'up'], ['.glyph-layout', 'up'],
    ['.download-controls', 'up'], ['.download-row', 'row', 45], ['.format-bundles', 'up'], ['.about-copy > *', 'up', 70], ['.help-list details', 'up', 70],
    ['.cta-panel', 'zoom'], ['.footer-cols > div', 'up', 80]];
  for (const [selector, kind, stagger] of plan) {
    $$(selector).forEach(el => {
      el.dataset.reveal = kind;
      if (stagger) el.style.setProperty('--delay', `${[...el.parentElement.children].indexOf(el) * stagger}ms`);
      revealObserver.observe(kind === 'wipe' ? el.parentElement : el);
    });
  }
} else {
  glyphs.seen = true;
}

// Buttons drift toward a nearby pointer
if (motionOK && finePointer) {
  const magnets = $$('[data-magnetic]');
  addEventListener('pointermove', event => {
    for (const el of magnets) {
      const box = el.getBoundingClientRect();
      const cx = box.left + box.width / 2, cy = box.top + box.height / 2;
      const dx = event.clientX - cx, dy = event.clientY - cy, reach = Math.max(box.width, box.height) * .9 + 30;
      if (Math.abs(dx) < reach && Math.abs(dy) < reach) {
        el.classList.add('is-near'); el.style.transform = `translate(${dx * .28}px, ${dy * .32}px)`;
      } else if (el.classList.contains('is-near')) {
        el.classList.remove('is-near'); el.style.transform = '';
      }
    }
  }, { passive: true });
}

// One frame loop for everything tied to scrolling
const bar = $('#scroll-progress');
let lastBar = '', lastHero = '';
function onFrame() {
  const y = scrollY, max = document.documentElement.scrollHeight - innerHeight;
  const barValue = (max > 0 ? y / max : 0).toFixed(4);
  if (barValue !== lastBar) { bar.style.transform = `scaleX(${barValue})`; lastBar = barValue; }
  const heroValue = clamp(y / (heroSection.offsetHeight * .9), 0, 1).toFixed(3);
  if (heroValue !== lastHero) { heroSection.style.setProperty('--hero-p', heroValue); lastHero = heroValue; }
  const box = statement.getBoundingClientRect();
  if (box.top < innerHeight && box.bottom > 0) {
    const progress = clamp((innerHeight * .88 - box.top) / (innerHeight * .5 + box.height * .6), 0, 1);
    const lit = Math.round(progress * statementWords.length);
    if (lit !== litWords) { statementWords.forEach((word, i) => word.classList.toggle('on', i < lit)); litWords = lit; }
  }
  requestAnimationFrame(onFrame);
}
if (motionOK) requestAnimationFrame(onFrame);
else addEventListener('scroll', () => { const max = document.documentElement.scrollHeight - innerHeight; bar.style.transform = `scaleX(${max > 0 ? scrollY / max : 0})`; }, { passive: true });

/* ---------------- Start ---------------- */
let resizeTimer;
addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => { resizePreview(); placeInspectorLine(); }, 120);
});
if (innerWidth <= 640) size.value = '52';
updateSize();
updatePreview();
fetch('catalog.json').then(response => {
  if (!response.ok) throw new Error('Catalog unavailable');
  return response.json();
}).then(data => { catalog = data; updateDownload(); }).catch(() => {
  $('#format-description').textContent = 'Format switching unavailable. TTF and ZIP links still work.';
});
function startFields() {
  resizePreview(); placeInspectorLine();
  if (hero.field) { hero.field.ready = true; showGreeting(0); hero.field.sync(); scheduleHero(); }
  if (ctaField) { ctaField.ready = true; if (ctaField.visible || !motionOK) ctaField.setText('AT-KPN', 'English', !motionOK); ctaField.sync(); }
}
Promise.all([300, 400, 700].map(weight => document.fonts.load(`${weight} 48px "AT-KPN"`))).then(loaded => {
  if (loaded.some(fonts => !fonts.length)) throw new Error('Font unavailable');
  startFields();
}).catch(() => {
  $('#font-status').textContent = 'Preview font could not load. Downloads remain available.';
  startFields();
});
