// Prototip (reference/obyektivka.html) dagi sof JS funksiyalarni node'da ishga tushiradi.
// Foydalanish: node scripts/js_reference.mjs < cases.json > results.json
//   cases.json: [{"fn": "lat2cyr", "args": ["Yo'q"]}, ...]
// Python port natijalari shu chiqish bilan solishtiriladi (tests/test_golden_js.py).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import vm from 'node:vm';

const here = path.dirname(fileURLToPath(import.meta.url));
const html = readFileSync(path.join(here, '..', '..', 'reference', 'obyektivka.html'), 'utf8');
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const lib = blocks.find(b => b.includes('function lat2cyr'));
if (!lib) throw new Error('lat2cyr topilmadi');

const ctx = vm.createContext({});
vm.runInContext(lib + `
;globalThis.__api = { lat2cyr, cyr2lat, lat2new, new2lat, convertScript, deepConvert,
  getTL, getUI, getSample, buildDocxFiles, TL_LAT, TL_RU, UI_LAT, UI_RU, SAMPLE_LAT, SAMPLE_RU };`, ctx);
const api = ctx.__api;

const special = {
  // getTL qaytargan obyektda funksiyalar bor — ularni ma'lumotga aylantiramiz
  davr: (lang, m) => api.getTL(lang).davr(m),
  relLines: (lang, name) => api.getTL(lang).relLines(name),
  deepConvertSample: (from, to) => api.deepConvert(api.getSample(from), from, to, ['photo', 'tugSana', 'lang']),
  getTL: lang => { const o = { ...api.getTL(lang) }; delete o.davr; delete o.relLines; return o; },
};

const input = JSON.parse(readFileSync(0, 'utf8'));
const out = input.map(({ fn, args }) => {
  const f = special[fn] || api[fn];
  if (typeof f !== 'function') throw new Error('noma\'lum funksiya: ' + fn);
  return JSON.parse(JSON.stringify(f(...args)));
});
process.stdout.write(JSON.stringify(out));
