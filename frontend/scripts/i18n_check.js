#!/usr/bin/env node
/**
 * i18n coverage check.
 *
 * The catalog falls back to English for any missing key, which is the right
 * runtime behaviour but hides gaps completely: switching to हिन्दी silently
 * shows English and nothing complains. This fails loudly instead.
 *
 *   node scripts/i18n_check.js
 *
 * Checks:
 *   1. Every key in `en` exists in `hi` and `pa`
 *   2. No key exists in hi/pa that isn't in en (dead keys)
 *   3. No value is accidentally left as the English string in hi/pa
 */

const fs = require('fs');
const path = require('path');

const FILE = path.join(__dirname, '..', 'src', 'i18n', 'translations.ts');
const src = fs.readFileSync(FILE, 'utf8');

/** Extract the `const <name>: Catalog = { ... };` block into a key→value map. */
function parseCatalog(name) {
  const start = src.indexOf(`const ${name}: Catalog = {`);
  if (start === -1) throw new Error(`Catalog '${name}' not found`);
  const open = src.indexOf('{', start);
  let depth = 0;
  let end = open;
  for (let i = open; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') {
      depth--;
      if (depth === 0) { end = i; break; }
    }
  }
  const body = src.slice(open + 1, end);

  const out = {};
  // Keys are quoted; values may be single- or multi-line strings.
  const re = /'([^']+)'\s*:\s*((?:'(?:[^'\\]|\\.)*'\s*)+),/g;
  let m;
  while ((m = re.exec(body)) !== null) {
    const value = m[2]
      .trim()
      .split(/'\s*\n\s*'/)          // concatenated multi-line literals
      .join('')
      .replace(/^'|'$/g, '');
    out[m[1]] = value;
  }
  return out;
}

// Keys whose value is DELIBERATELY identical across languages — product and
// brand names are not translated, so flagging them as "still English" is noise.
const SAME_BY_DESIGN = new Set([
  'auth.secureWealthId',
]);

const en = parseCatalog('en');
const hi = parseCatalog('hi');
const pa = parseCatalog('pa');

const G = '\x1b[32m', R = '\x1b[31m', Y = '\x1b[33m', B = '\x1b[1m', N = '\x1b[0m';
let failures = 0;

console.log(`${B}i18n coverage check${N}`);
console.log(`  en: ${Object.keys(en).length} keys`);

for (const [code, cat] of [['hi', hi], ['pa', pa]]) {
  const missing = Object.keys(en).filter((k) => !(k in cat));
  const extra = Object.keys(cat).filter((k) => !(k in en));
  // Identical to English usually means someone forgot to translate. Short
  // strings and brand names legitimately match, so only flag longer text.
  const untranslated = Object.keys(cat).filter(
    (k) =>
      k in en &&
      cat[k] === en[k] &&
      en[k].length > 12 &&
      !SAME_BY_DESIGN.has(k)
  );

  if (missing.length === 0 && extra.length === 0 && untranslated.length === 0) {
    console.log(`${G}  ✔ ${code}: complete (${Object.keys(cat).length} keys)${N}`);
    continue;
  }
  failures++;
  console.log(`${R}  ✘ ${code}:${N}`);
  if (missing.length) {
    console.log(`${R}      ${missing.length} missing:${N} ${missing.slice(0, 8).join(', ')}${missing.length > 8 ? ` … +${missing.length - 8}` : ''}`);
  }
  if (extra.length) {
    console.log(`${Y}      ${extra.length} not in en:${N} ${extra.slice(0, 8).join(', ')}`);
  }
  if (untranslated.length) {
    console.log(`${Y}      ${untranslated.length} still English:${N} ${untranslated.slice(0, 8).join(', ')}`);
  }
}

console.log('────────────────────────────────────────');
if (failures) {
  console.log(`${R}i18n incomplete — switching language would show English in places.${N}`);
  process.exit(1);
}
console.log(`${G}All languages complete.${N}`);
