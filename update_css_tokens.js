const fs = require('fs');
const path = 'src/app/globals.css';
let css = fs.readFileSync(path, 'utf8');

const newRootBlock = `
:root {
  /* === OTA Navy+Gold Ottoman Palette === */
  --ota-bg-1: #06151D;
  --ota-bg-2: #081D26;
  --ota-card: #0A202A;
  --ota-elevated: #0E2731;
  --ota-border: rgba(215,165,72,0.20);
  --ota-border-hover: rgba(215,165,72,0.38);
  --ota-gold: #D7A548;
  --ota-gold-light: #EDC46F;
  --ota-gold-dim: rgba(215,165,72,0.12);
  --ota-text: #F1EEE7;
  --ota-text-2: #AAB7BA;
  --ota-text-muted: #718488;
  --ota-teal-active: rgba(30,107,123,0.35);
  --ota-sidebar-w: 240px;
  --ota-header-h: 72px;

  /* === Legacy aliases (used by existing CSS) === */
  --bg-primary: #06151D;
  --bg-secondary: #081D26;
  --bg-tertiary: #0A202A;
  --bg-sidebar: #06151D;
  --surface: #0A202A;
  --surface-hover: #0E2731;
  --surface-active: #123040;
  --gold-50: #fdf8ed;
  --gold-100: #f9edcb;
  --gold-200: #f3d992;
  --gold-300: #EDC46F;
  --gold-400: #D7A548;
  --gold-500: #C4922F;
  --gold-600: #a57a22;
  --gold-700: #7d6118;
  --gold-800: #634c14;
  --gold-900: #4a3810;
  --text-primary: #F1EEE7;
  --text-secondary: #AAB7BA;
  --text-muted: #718488;
  --text-accent: #D7A548;
  --border: rgba(215,165,72,0.20);
  --border-subtle: rgba(215,165,72,0.12);
  --border-accent: rgba(215,165,72,0.28);
  --success: #22c55e;
  --success-bg: rgba(34,197,94,0.12);
  --warning: #f59e0b;
  --warning-bg: rgba(245,158,11,0.12);
  --error: #ef4444;
  --error-bg: rgba(239,68,68,0.12);
  --info: #3b82f6;
  --info-bg: rgba(59,130,246,0.12);
  --glass-bg: rgba(10,32,42,0.80);
  --glass-border: rgba(215,165,72,0.15);
  --glass-shadow: 0 4px 32px rgba(0,0,0,0.6);
  --transition-fast: 150ms ease;
  --transition-base: 220ms ease;
  --transition-slow: 350ms ease;
  --sidebar-width: 240px;
  --sidebar-collapsed: 64px;
  --header-height: 72px;
  --accent-gold: #D7A548;
  --text-dim: #718488;
}
`.trim();

// Replace the entire :root block (greedy match to closing brace)
css = css.replace(/:root\s*\{[\s\S]*?\}/, newRootBlock);

fs.writeFileSync(path, css, 'utf8');
console.log('CSS :root tokens updated - palette changed to navy+gold');
