#!/usr/bin/env node
/**
 * Accessibility lint (M7, task 23).
 *
 *   node scripts/a11y_check.js
 *
 * Catches the two failures that actually lock people out of a banking app:
 *
 *   1. ICON-ONLY BUTTONS WITH NO LABEL
 *      A TouchableOpacity containing only an icon announces nothing to a
 *      screen reader — the user hears "button" and has to guess. Buttons with
 *      visible <Text> are fine: React Native reads the text automatically.
 *
 *   2. SMALL TAP TARGETS
 *      An icon rendered at 16-20px is a ~20px target. Both Apple (44pt) and
 *      Android (48dp) require larger. `hitSlop` fixes it without changing the
 *      visual design, so we require it on icon-only controls.
 *
 * Deliberately NOT checked: colour contrast. It needs the rendered palette and
 * would be guesswork from source. Tracked as a manual step in TESTING.md.
 */

const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', 'src');
// Deprecated screens kept only as commented-out reference (M5).
const SKIP = ['AuditDashboardScreen.tsx', 'HashChainVisual.tsx'];

const G = '\x1b[32m', R = '\x1b[31m', Y = '\x1b[33m', B = '\x1b[1m', N = '\x1b[0m';

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, out);
    else if (entry.name.endsWith('.tsx') && !SKIP.includes(entry.name)) out.push(full);
  }
  return out;
}

/** Split a file into balanced <TouchableOpacity>…</TouchableOpacity> blocks. */
function touchables(src) {
  const blocks = [];
  const re = /<TouchableOpacity\b/g;
  let m;
  while ((m = re.exec(src)) !== null) {
    const close = src.indexOf('</TouchableOpacity>', m.index);
    // Self-closing (rare here) or unterminated — skip rather than mis-report.
    if (close === -1) continue;
    blocks.push({
      text: src.slice(m.index, close + '</TouchableOpacity>'.length),
      line: src.slice(0, m.index).split('\n').length,
    });
  }
  return blocks;
}

let unlabelled = 0;
let smallTarget = 0;
let checked = 0;

console.log(`${B}Accessibility check${N}`);

for (const file of walk(SRC)) {
  const src = fs.readFileSync(file, 'utf8');
  const rel = path.relative(path.join(__dirname, '..'), file);

  for (const { text, line } of touchables(src)) {
    // A button with visible text labels itself.
    if (/<Text\b/.test(text)) continue;
    // Full-screen invisible overlays used to dismiss modals are decoration.
    if (/StyleSheet\.absoluteFill/.test(text)) continue;
    checked++;

    const hasLabel = /accessibilityLabel|accessibilityHint/.test(text);
    const hasSlop = /hitSlop/.test(text);

    if (!hasLabel) {
      unlabelled++;
      console.log(`${R}  ✘ ${rel}:${line} — icon-only button with no accessibilityLabel${N}`);
    }
    if (!hasSlop) {
      smallTarget++;
      console.log(`${Y}  ! ${rel}:${line} — icon-only button with no hitSlop (tap target likely under 44px)${N}`);
    }
  }
}

console.log('────────────────────────────────────────');
console.log(`  Icon-only buttons checked: ${checked}`);
if (unlabelled === 0 && smallTarget === 0) {
  console.log(`${G}All icon-only controls are labelled and reachable.${N}`);
  process.exit(0);
}
console.log(`  ${R}Unlabelled: ${unlabelled}${N}   ${Y}Small target: ${smallTarget}${N}`);
process.exit(unlabelled > 0 ? 1 : 0);
