const state = { language: 'English', weight: 'Bold', format: 'TTF', theme: 'paper', texts: new Map() };
const weights = { Light: 300, Regular: 400, Bold: 700 };
const examples = {
  English: { tag: 'en', sample: 'Hello, world.' },
  Kannada: { tag: 'kn', sample: 'ನಮಸ್ಕಾರ' },
  Hindi: { tag: 'hi', sample: 'नमस्ते' },
  Marathi: { tag: 'mr', sample: 'नमस्कार' },
  Malayalam: { tag: 'ml', sample: 'നമസ്കാരം' },
  Tamil: { tag: 'ta', sample: 'வணக்கம்' },
  Telugu: { tag: 'te', sample: 'నమస్కారం' },
  Bengali: { tag: 'bn', sample: 'নমস্কার' },
};
const descriptions = { TTF: 'TrueType · for desktop apps', OTF: 'OpenType CFF · for desktop apps', WOFF2: 'WOFF2 · compact web fonts', WOFF: 'WOFF · web font fallback' };
const preview = document.querySelector('#preview-text');
const size = document.querySelector('#font-size');
const studio = document.querySelector('.type-studio');
const currentDownload = document.querySelector('#current-download');
let catalog;

function resizePreview() {
  preview.style.height = 'auto';
  preview.style.height = `${Math.min(620, Math.max(innerWidth < 761 ? 175 : 220, preview.scrollHeight))}px`;
}
function updateDownload() {
  const row = catalog?.languages.find(item => item.id === state.language);
  if (row) currentDownload.href = row.fonts[state.weight][state.format].path;
  currentDownload.textContent = `Download ${state.language} ${state.weight} · ${state.format}`;
}
function updateProofs() {
  const sample = preview.value || examples[state.language].sample;
  document.querySelectorAll('[data-proof-weight]').forEach(proof => {
    proof.textContent = sample;
    proof.lang = examples[state.language].tag;
    proof.style.fontFeatureSettings = preview.style.fontFeatureSettings;
  });
}
function updatePreview() {
  preview.lang = examples[state.language].tag;
  preview.style.fontWeight = weights[state.weight];
  preview.style.fontFeatureSettings = state.language === 'Malayalam' && document.querySelector('#stacked-form').checked ? '"ss01" 1' : '"ss01" 0';
  document.querySelector('#preview-caption').textContent = `AT-KPN ${state.language} · ${state.weight} ${weights[state.weight]}`;
  document.querySelector('#malayalam-option').hidden = state.language !== 'Malayalam';
  updateProofs();
  updateDownload();
  resizePreview();
}
document.querySelectorAll('[data-lang]').forEach(button => button.addEventListener('click', () => {
  state.texts.set(state.language, preview.value);
  state.language = button.dataset.lang;
  preview.value = state.texts.has(state.language) ? state.texts.get(state.language) : examples[state.language].sample;
  document.querySelectorAll('[data-lang]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  updatePreview();
}));
document.querySelectorAll('.weight-control [data-weight]').forEach(button => button.addEventListener('click', () => {
  state.weight = button.dataset.weight;
  document.querySelectorAll('.weight-control [data-weight]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  updatePreview();
}));
document.querySelectorAll('.color-control [data-theme]').forEach(button => button.addEventListener('click', () => {
  state.theme = button.dataset.theme;
  studio.dataset.theme = state.theme;
  document.querySelectorAll('.color-control [data-theme]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
}));
function updateSize() {
  preview.style.fontSize = `${size.value}px`;
  document.querySelector('#size-output').textContent = `${size.value} px`;
  resizePreview();
}
size.addEventListener('input', updateSize);
preview.addEventListener('input', () => { state.texts.set(state.language, preview.value); updateProofs(); resizePreview(); });
document.querySelector('#stacked-form').addEventListener('change', updatePreview);
document.querySelector('#reset-text').addEventListener('click', () => {
  preview.value = examples[state.language].sample;
  state.texts.delete(state.language);
  updatePreview();
});
document.querySelectorAll('[data-format]').forEach(button => button.addEventListener('click', () => {
  if (!catalog) return;
  state.format = button.dataset.format;
  document.querySelectorAll('[data-format]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  document.querySelector('#format-description').textContent = descriptions[state.format];
  document.querySelectorAll('.download-row').forEach(row => {
    const language = catalog.languages.find(item => item.id === row.dataset.language);
    row.querySelectorAll('.weight-download').forEach(link => {
      link.href = language.fonts[link.dataset.weight][state.format].path;
      link.setAttribute('aria-label', `Download ${language.name} ${link.dataset.weight} ${state.format}`);
      link.querySelector('span').textContent = state.format;
    });
  });
  updateDownload();
}));
document.querySelector('#copy-css').addEventListener('click', async () => {
  const status = document.querySelector('#copy-status');
  try {
    await navigator.clipboard.writeText(document.querySelector('#web-code').textContent);
    status.textContent = 'Code copied.';
  } catch {
    status.textContent = 'Select the code above and copy it manually.';
  }
});
window.addEventListener('resize', resizePreview);
if (innerWidth < 761) size.value = '52';
updateSize();
updatePreview();
fetch('catalog.json').then(response => {
  if (!response.ok) throw new Error('Catalog unavailable');
  return response.json();
}).then(data => { catalog = data; updateDownload(); }).catch(() => {
  document.querySelector('#format-description').textContent = 'Format switching unavailable. TTF and ZIP links still work.';
});
Promise.all([300,400,700].map(weight => document.fonts.load(`${weight} 48px "AT-KPN"`))).then(loaded => {
  if (loaded.some(fonts => !fonts.length)) throw new Error('Font unavailable');
  resizePreview();
}).catch(() => { document.querySelector('#font-status').textContent = 'Preview font could not load. Downloads remain available.'; });
