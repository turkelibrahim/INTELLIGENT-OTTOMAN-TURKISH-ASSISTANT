const fs = require('fs');
const path = 'src/app/globals.css';
let css = fs.readFileSync(path, 'utf8');

const newCss = `

/* =====================================================
   OTA — NEW COMPONENT SYSTEM (Navy+Gold Ottoman UI)
   ===================================================== */

/* ── App Shell ─────────────────────────────────────── */
.ota-shell {
  display: flex;
  min-height: 100vh;
  background: var(--ota-bg-1);
}

.ota-main-wrapper {
  margin-left: var(--ota-sidebar-w);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  overflow-x: hidden;
}

.ota-content-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

/* ── Sidebar ────────────────────────────────────────── */
.ota-sidebar {
  width: var(--ota-sidebar-w);
  background: var(--ota-bg-1);
  border-right: 1px solid var(--ota-border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0; left: 0; bottom: 0;
  z-index: 50;
  overflow-y: auto;
  overflow-x: hidden;
}

.ota-sidebar-logo {
  padding: 20px 16px 16px;
  border-bottom: 1px solid var(--ota-border);
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.ota-logo-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--ota-card), var(--ota-elevated));
  border: 1px solid var(--ota-border);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--ota-gold);
}

.ota-logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.ota-logo-main {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--ota-text);
}

.ota-logo-sub {
  font-size: 9px;
  font-weight: 500;
  letter-spacing: 0.08em;
  color: var(--ota-gold);
  margin-top: 1px;
}

.ota-sidebar-nav {
  flex: 1;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow-y: auto;
}

.ota-nav-group {
  margin-bottom: 4px;
}

.ota-nav-group-label {
  display: block;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ota-text-muted);
  padding: 12px 12px 4px;
}

.ota-nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px 9px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--ota-text-2);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-decoration: none;
  margin-bottom: 2px;
  border: 1px solid transparent;
}

.ota-nav-item:hover {
  color: var(--ota-text);
  background: rgba(215,165,72,0.06);
  border-color: var(--ota-border);
}

.ota-nav-item.active {
  color: var(--ota-gold);
  background: var(--ota-teal-active);
  border-color: rgba(215,165,72,0.20);
}

.ota-nav-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--ota-gold);
  border-radius: 0 2px 2px 0;
}

.ota-nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: inherit;
  opacity: 0.75;
}

.ota-nav-item.active .ota-nav-icon {
  opacity: 1;
  color: var(--ota-gold);
}

.ota-nav-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ota-sidebar-footer {
  padding: 12px;
  flex-shrink: 0;
}

.ota-sidebar-pattern {
  height: 40px;
  opacity: 0.08;
  background-image: repeating-linear-gradient(
    45deg,
    var(--ota-gold) 0, var(--ota-gold) 1px,
    transparent 0, transparent 50%
  );
  background-size: 8px 8px;
  border-radius: 8px;
}

/* ── Header ─────────────────────────────────────────── */
.ota-header {
  height: var(--ota-header-h);
  background: var(--ota-bg-2);
  border-bottom: 1px solid var(--ota-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 40;
  gap: 16px;
  overflow: hidden;
}

.ota-header-pattern {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(ellipse 50% 100% at 70% 50%, rgba(215,165,72,0.04) 0%, transparent 70%);
  pointer-events: none;
}

.ota-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  min-width: 200px;
}

.ota-header-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--ota-text);
  margin: 0;
  line-height: 1.2;
  letter-spacing: 0.01em;
}

.ota-header-subtitle {
  font-size: 11px;
  color: var(--ota-gold);
  margin: 2px 0 0;
  opacity: 0.85;
}

.ota-header-center {
  flex: 1;
  max-width: 520px;
}

.ota-search-form {
  position: relative;
  display: flex;
  align-items: center;
}

.ota-search-icon {
  position: absolute;
  left: 12px;
  color: var(--ota-text-muted);
  pointer-events: none;
  display: flex;
  align-items: center;
}

.ota-search-input {
  width: 100%;
  background: rgba(10,32,42,0.6);
  border: 1px solid var(--ota-border);
  border-radius: 8px;
  padding: 8px 14px 8px 36px;
  font-size: 13px;
  color: var(--ota-text);
  outline: none;
  transition: all var(--transition-fast);
}

.ota-search-input::placeholder {
  color: var(--ota-text-muted);
}

.ota-search-input:focus {
  border-color: var(--ota-gold);
  background: rgba(10,32,42,0.85);
  box-shadow: 0 0 0 2px rgba(215,165,72,0.12);
}

.ota-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.ota-date-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(10,32,42,0.5);
  border: 1px solid var(--ota-border);
  border-radius: 8px;
}

.ota-date-icon {
  color: var(--ota-gold);
  opacity: 0.8;
  display: flex;
}

.ota-date-info {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}

.ota-date-hijri {
  font-size: 11px;
  font-weight: 600;
  color: var(--ota-gold);
}

.ota-date-miladi {
  font-size: 10px;
  color: var(--ota-text-muted);
}

.ota-header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ota-icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid var(--ota-border);
  background: rgba(10,32,42,0.5);
  color: var(--ota-text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
}

.ota-icon-btn:hover {
  background: rgba(215,165,72,0.08);
  border-color: var(--ota-border-hover);
  color: var(--ota-gold);
}

.ota-notif-dot {
  position: absolute;
  top: 7px; right: 7px;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--warning);
  border: 1px solid var(--ota-bg-2);
}

/* ── Dashboard Layout ───────────────────────────────── */
.ota-dashboard {
  min-height: 100%;
  padding: 0;
}

/* ── Welcome / Empty State ──────────────────────────── */
.ota-welcome {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - var(--ota-header-h));
  padding: 40px 24px;
}

.ota-welcome-inner {
  max-width: 520px;
  width: 100%;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.ota-welcome-icon {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: var(--ota-card);
  border: 1px solid var(--ota-border);
  display: flex;
  align-items: center;
  justify-content: center;
}

.ota-welcome-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--ota-text);
  margin: 0;
  line-height: 1.3;
}

.ota-welcome-desc {
  font-size: 14px;
  color: var(--ota-text-2);
  line-height: 1.6;
  margin: 0;
  max-width: 420px;
}

/* ── Dropzone ───────────────────────────────────────── */
.ota-dropzone {
  width: 100%;
  border: 2px dashed var(--ota-border);
  border-radius: 16px;
  padding: 40px 24px;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-base);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  background: rgba(10,32,42,0.3);
}

.ota-dropzone:hover,
.ota-dropzone.dragging {
  border-color: var(--ota-gold);
  background: rgba(215,165,72,0.04);
}

.ota-dropzone-icon {
  font-size: 28px;
  color: var(--ota-gold);
  opacity: 0.6;
}

.ota-dropzone-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--ota-gold);
}

.ota-dropzone-hint {
  font-size: 12px;
  color: var(--ota-text-muted);
}

/* ── Upload form bar ────────────────────────────────── */
.ota-upload-form-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  background: var(--ota-card);
  border-bottom: 1px solid var(--ota-border);
  flex-wrap: wrap;
}

.ota-upload-file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.ota-file-icon { font-size: 18px; }

.ota-file-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--ota-text);
}

.ota-file-size {
  font-size: 11px;
  color: var(--ota-text-muted);
}

.ota-upload-fields {
  display: flex;
  gap: 8px;
  flex: 1;
  min-width: 300px;
}

.ota-upload-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* ── Input ──────────────────────────────────────────── */
.ota-input {
  background: var(--ota-bg-1);
  border: 1px solid var(--ota-border);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--ota-text);
  outline: none;
  transition: all var(--transition-fast);
  width: 100%;
}

.ota-input::placeholder { color: var(--ota-text-muted); }

.ota-input:focus {
  border-color: var(--ota-gold);
  box-shadow: 0 0 0 2px rgba(215,165,72,0.10);
}

/* ── Processing banner ──────────────────────────────── */
.ota-processing-banner {
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.ota-processing-note {
  font-size: 13px;
  color: var(--ota-text-muted);
  text-align: center;
}

/* ── Analysis Progress ──────────────────────────────── */
.ota-analysis-progress {
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
}

.ota-progress-steps {
  display: flex;
  align-items: center;
  gap: 0;
}

.ota-progress-step-wrap {
  display: flex;
  align-items: center;
  flex: 1;
}

.ota-progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.ota-step-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid var(--ota-border);
  background: var(--ota-card);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: var(--ota-text-muted);
  transition: all var(--transition-base);
}

.ota-progress-step.done .ota-step-dot {
  background: var(--success);
  border-color: var(--success);
  color: #fff;
}

.ota-progress-step.active .ota-step-dot {
  border-color: var(--ota-gold);
  color: var(--ota-gold);
  box-shadow: 0 0 0 4px rgba(215,165,72,0.15);
  animation: pulse-gold 1.5s ease infinite;
}

@keyframes pulse-gold {
  0%, 100% { box-shadow: 0 0 0 4px rgba(215,165,72,0.15); }
  50%       { box-shadow: 0 0 0 8px rgba(215,165,72,0.08); }
}

.ota-step-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--ota-text-muted);
  text-align: center;
  white-space: nowrap;
}

.ota-progress-step.active .ota-step-label,
.ota-progress-step.done .ota-step-label {
  color: var(--ota-text-2);
}

.ota-step-sub {
  font-size: 10px;
  color: var(--ota-gold);
}

.ota-step-connector {
  flex: 1;
  height: 2px;
  background: var(--ota-border);
  margin: 0 4px;
  margin-bottom: 16px;
}

.ota-step-connector.done {
  background: var(--success);
}

.ota-progress-error {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--error-bg);
  border: 1px solid rgba(239,68,68,0.25);
  border-radius: 10px;
  color: #f87171;
  font-size: 13px;
}

/* ── Error banner ───────────────────────────────────── */
.ota-error-banner {
  margin: 24px;
  padding: 20px;
  background: var(--error-bg);
  border: 1px solid rgba(239,68,68,0.25);
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.ota-error-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.ota-error-icon {
  font-size: 20px;
  color: var(--error);
  flex-shrink: 0;
}

/* ── Alert ──────────────────────────────────────────── */
.ota-alert {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  width: 100%;
}

.ota-alert.error {
  background: var(--error-bg);
  border: 1px solid rgba(239,68,68,0.25);
  color: #f87171;
}

/* ── Workspace ──────────────────────────────────────── */
.ota-workspace {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.ota-workspace-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: var(--ota-bg-2);
  border-bottom: 1px solid var(--ota-border);
  flex-shrink: 0;
}

.ota-workspace-doc-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ota-workspace-filename {
  font-size: 13px;
  font-weight: 600;
  color: var(--ota-text);
}

.ota-workspace-doctype {
  font-size: 11px;
  color: var(--ota-gold);
  background: rgba(215,165,72,0.10);
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid rgba(215,165,72,0.20);
}

.ota-workspace-actions {
  display: flex;
  gap: 8px;
}

/* ── Three Panel Grid ───────────────────────────────── */
.ota-three-panel-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0;
  border-bottom: 1px solid var(--ota-border);
  min-height: 520px;
  max-height: 680px;
  flex-shrink: 0;
}

/* ── Panel ──────────────────────────────────────────── */
.ota-panel {
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--ota-border);
  background: var(--ota-card);
  overflow: hidden;
}

.ota-panel:last-child { border-right: none; }

.ota-panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 12px 14px 10px;
  border-bottom: 1px solid var(--ota-border);
  background: var(--ota-elevated);
  flex-shrink: 0;
  gap: 8px;
  min-height: 56px;
}

.ota-panel-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--ota-text);
  margin: 0;
  line-height: 1.2;
}

.ota-panel-subtitle {
  font-size: 10px;
  color: var(--ota-text-muted);
  display: block;
  margin-top: 2px;
}

.ota-panel-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.ota-panel-header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
}

.ota-panel-actions {
  display: flex;
  gap: 4px;
}

.ota-viewer-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid var(--ota-border);
  background: var(--ota-bg-2);
  color: var(--ota-text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 13px;
  transition: all var(--transition-fast);
  padding: 0;
  flex-shrink: 0;
}

.ota-viewer-btn:hover {
  background: rgba(215,165,72,0.08);
  border-color: var(--ota-border-hover);
  color: var(--ota-gold);
}

.ota-zoom-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--ota-text-muted);
  padding: 0 4px;
  min-width: 36px;
  text-align: center;
}

/* ── Viewer Body ────────────────────────────────────── */
.ota-viewer-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #030d12;
  cursor: grab;
  position: relative;
}

.ota-viewer-body:active { cursor: grabbing; }

.ota-viewer-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: transform 0.1s;
  user-select: none;
  -webkit-user-drag: none;
}

.ota-viewer-pdf-placeholder {
  font-size: 14px;
  color: var(--ota-text-muted);
  text-align: center;
}

/* ── Panel Body (text panels) ───────────────────────── */
.ota-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
}

.ota-ottomanic-text {
  font-family: 'Noto Naskh Arabic', 'Traditional Arabic', 'Times New Roman', serif;
  font-size: 16px;
  line-height: 2;
}

/* ── Text lines ─────────────────────────────────────── */
.ota-text-line {
  display: flex;
  gap: 10px;
  padding: 4px 14px;
  cursor: pointer;
  transition: background var(--transition-fast);
  border-left: 2px solid transparent;
  margin: 0;
}

.ota-text-line:hover {
  background: rgba(215,165,72,0.05);
}

.ota-text-line.active {
  background: rgba(215,165,72,0.10);
  border-left-color: var(--ota-gold);
}

.ota-line-num {
  font-size: 11px;
  font-weight: 600;
  color: var(--ota-gold);
  opacity: 0.5;
  min-width: 24px;
  flex-shrink: 0;
  line-height: 2;
  font-family: monospace;
}

.ota-text-line.active .ota-line-num { opacity: 1; }

.ota-line-text {
  flex: 1;
  color: var(--ota-text);
  font-size: 14px;
}

.ota-panel-body.ota-ottomanic-text .ota-line-text {
  font-size: 16px;
  direction: rtl;
}

/* ── Inline editor ──────────────────────────────────── */
.ota-inline-editor {
  padding: 10px 14px;
  background: var(--ota-bg-1);
  border-bottom: 1px solid var(--ota-border);
}

.ota-edit-textarea {
  width: 100%;
  background: var(--ota-card);
  border: 1px solid var(--ota-gold);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  color: var(--ota-text);
  outline: none;
  resize: vertical;
  font-family: 'Noto Naskh Arabic', serif;
}

.ota-edit-status {
  font-size: 11px;
  color: var(--ota-gold);
  display: block;
  margin-top: 6px;
}

/* ── Latin section ──────────────────────────────────── */
.ota-latin-section {
  border-bottom: 1px solid var(--ota-border);
  background: var(--ota-bg-2);
  flex-shrink: 0;
}

.ota-latin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  cursor: pointer;
  user-select: none;
}

.ota-latin-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ota-latin-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--ota-text);
}

.ota-latin-body {
  padding: 0 20px 16px;
  border-top: 1px solid var(--ota-border);
}

.ota-latin-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
}

.ota-latin-scroll {
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ota-latin-line {
  display: flex;
  gap: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.ota-latin-line:hover { background: rgba(215,165,72,0.05); }
.ota-latin-line.active { background: rgba(215,165,72,0.10); }

.ota-latin-text {
  font-size: 13px;
  color: var(--ota-text);
  line-height: 1.6;
}

.ota-empty-text {
  font-size: 13px;
  color: var(--ota-text-muted);
  text-align: center;
  padding: 16px;
}

/* ── Document Tabs ──────────────────────────────────── */
.ota-doc-tabs-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.ota-tabs-nav {
  display: flex;
  border-bottom: 1px solid var(--ota-border);
  background: var(--ota-bg-2);
  flex-shrink: 0;
  overflow-x: auto;
}

.ota-tab {
  padding: 13px 18px;
  font-size: 12px;
  font-weight: 600;
  color: var(--ota-text-muted);
  border: none;
  background: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
  letter-spacing: 0.02em;
}

.ota-tab:hover { color: var(--ota-text-2); }

.ota-tab.active {
  color: var(--ota-gold);
  border-bottom-color: var(--ota-gold);
}

.ota-tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--ota-card);
  min-height: 240px;
  max-height: 480px;
}

/* ── Buttons ────────────────────────────────────────── */
.ota-btn-primary {
  background: var(--ota-gold);
  color: #06151D;
  font-weight: 700;
  font-size: 13px;
  padding: 9px 18px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.ota-btn-primary:hover:not(:disabled) {
  background: var(--ota-gold-light);
  transform: translateY(-1px);
}

.ota-btn-primary:disabled { opacity: 0.45; cursor: not-allowed; }

.ota-btn-primary.small {
  padding: 6px 12px;
  font-size: 12px;
}

.ota-btn-secondary {
  background: var(--ota-card);
  color: var(--ota-text);
  font-weight: 600;
  font-size: 13px;
  padding: 9px 18px;
  border-radius: 8px;
  border: 1px solid var(--ota-border-hover);
  cursor: pointer;
  transition: all var(--transition-fast);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.ota-btn-secondary:hover:not(:disabled) {
  border-color: var(--ota-gold);
  color: var(--ota-gold);
}

.ota-btn-secondary:disabled { opacity: 0.45; cursor: not-allowed; }

.ota-btn-ghost {
  background: transparent;
  color: var(--ota-text-2);
  font-size: 13px;
  font-weight: 500;
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid var(--ota-border);
  cursor: pointer;
  transition: all var(--transition-fast);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.ota-btn-ghost:hover:not(:disabled) {
  color: var(--ota-text);
  border-color: var(--ota-border-hover);
  background: rgba(215,165,72,0.06);
}

.ota-btn-ghost:disabled { opacity: 0.45; cursor: not-allowed; }

.ota-btn-ghost.small {
  padding: 5px 10px;
  font-size: 12px;
}

/* ── Badges ─────────────────────────────────────────── */
.ota-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.ota-badge.small {
  font-size: 10px;
  padding: 2px 7px;
}

.ota-badge-success { background: var(--success-bg); color: #4ade80; }
.ota-badge-warning { background: var(--warning-bg); color: #fbbf24; }
.ota-badge-error   { background: var(--error-bg);   color: #f87171; }
.ota-badge-info    { background: var(--info-bg);     color: #60a5fa; }
.ota-badge-neutral { background: rgba(113,132,136,0.15); color: var(--ota-text-muted); }
.ota-badge-gold    { background: rgba(215,165,72,0.12);  color: var(--ota-gold); }

/* ── Confidence Badge ───────────────────────────────── */
.ota-confidence-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  font-family: monospace;
}

.ota-confidence-badge.small {
  font-size: 10px;
  padding: 2px 6px;
}

.ota-confidence-badge.high   { background: var(--success-bg); color: #4ade80; }
.ota-confidence-badge.medium { background: var(--warning-bg); color: #fbbf24; }
.ota-confidence-badge.low    { background: var(--error-bg);   color: #f87171; }

/* ── Empty State ────────────────────────────────────── */
.ota-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  text-align: center;
  gap: 10px;
}

.ota-empty-state.compact {
  padding: 20px 16px;
}

.ota-empty-icon {
  font-size: 28px;
  color: var(--ota-text-muted);
  opacity: 0.5;
}

.ota-empty-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ota-text-2);
  margin: 0;
}

.ota-empty-desc {
  font-size: 12px;
  color: var(--ota-text-muted);
  margin: 0;
  max-width: 280px;
  line-height: 1.5;
}

.ota-empty-action {
  margin-top: 4px;
}

/* ── Document Info Tab ──────────────────────────────── */
.ota-doc-info-tab {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ota-info-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.ota-info-row {
  display: grid;
  grid-template-columns: 160px 1fr auto;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--ota-border);
}

.ota-info-row.missing { opacity: 0.5; }

.ota-info-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--ota-text-muted);
  flex-shrink: 0;
}

.ota-info-value {
  font-size: 13px;
  color: var(--ota-text);
  font-weight: 500;
}

.ota-info-value.muted { color: var(--ota-text-muted); }

.ota-info-badges {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.ota-info-section-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ota-text-muted);
  display: block;
  margin-bottom: 8px;
}

.ota-info-inferred-section,
.ota-info-missing-section {
  padding-top: 8px;
}

.ota-info-missing-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: rgba(113,132,136,0.08);
  border-radius: 8px;
  border: 1px solid var(--ota-border);
}

.ota-info-missing-text {
  font-size: 12px;
  color: var(--ota-text-muted);
}

/* ── Entities Tab ───────────────────────────────────── */
.ota-entities-tab {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ota-entity-filters {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.ota-filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--ota-border);
  background: transparent;
  font-size: 12px;
  font-weight: 500;
  color: var(--ota-text-2);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.ota-filter-chip:hover {
  border-color: var(--ota-border-hover);
  color: var(--ota-text);
}

.ota-filter-chip.active {
  background: rgba(215,165,72,0.12);
  border-color: var(--ota-gold);
  color: var(--ota-gold);
}

.ota-filter-count {
  background: rgba(255,255,255,0.1);
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 10px;
}

.ota-entity-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ota-entity-group { display: flex; flex-direction: column; gap: 6px; }

.ota-entity-group-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ota-entity-group-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.10em;
  text-transform: uppercase;
  color: var(--ota-gold);
}

.ota-entity-group-count {
  font-size: 10px;
  color: var(--ota-text-muted);
  background: rgba(215,165,72,0.10);
  padding: 1px 6px;
  border-radius: 999px;
}

.ota-entity-card {
  padding: 12px 14px;
  background: var(--ota-elevated);
  border: 1px solid var(--ota-border);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: border-color var(--transition-fast);
}

.ota-entity-card:hover { border-color: var(--ota-border-hover); }

.ota-entity-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--ota-text);
}

.ota-entity-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.ota-entity-type {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ota-gold);
}

.ota-entity-location {
  font-size: 11px;
  color: var(--ota-text-muted);
}

.ota-entity-source {
  font-size: 11px;
  color: var(--ota-text-muted);
}

.ota-marks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
}

.ota-mark-card {
  padding: 12px;
  background: var(--ota-elevated);
  border: 1px solid var(--ota-border);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ota-mark-type {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--ota-gold);
  letter-spacing: 0.08em;
}

.ota-mark-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--ota-text);
}

.ota-mark-source {
  font-size: 11px;
  color: var(--ota-text-muted);
}

/* ── Historical Tab ─────────────────────────────────── */
.ota-historical-tab {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ota-low-confidence-warning {
  padding: 20px;
  background: var(--warning-bg);
  border: 1px solid rgba(245,158,11,0.25);
  border-radius: 12px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.ota-warning-icon {
  font-size: 24px;
  color: var(--warning);
}

.ota-low-confidence-warning h3 {
  font-size: 15px;
  font-weight: 700;
  color: var(--ota-text);
  margin: 0;
}

.ota-low-confidence-warning p {
  font-size: 13px;
  color: var(--ota-text-2);
  margin: 0;
  max-width: 400px;
  line-height: 1.5;
}

.ota-warning-suggestion {
  font-style: italic;
}

.ota-historical-context {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ota-historical-paragraph {
  font-size: 14px;
  line-height: 1.7;
  color: var(--ota-text);
  margin: 0;
}

.ota-historical-stats {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  padding: 14px 0;
  border-top: 1px solid var(--ota-border);
}

.ota-historical-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ota-stat-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--ota-gold);
}

.ota-stat-label {
  font-size: 11px;
  color: var(--ota-text-muted);
}

.ota-stat-badge.warning {
  background: var(--warning-bg);
  color: #fbbf24;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
}

.ota-historical-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(245,158,11,0.06);
  border: 1px solid rgba(245,158,11,0.20);
  border-radius: 8px;
  font-size: 12px;
  color: var(--ota-text-2);
}

/* ── Sources Tab ────────────────────────────────────── */
.ota-sources-tab {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ota-sources-count {
  font-size: 12px;
  color: var(--ota-text-muted);
}

.ota-sources-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ota-source-card {
  padding: 14px;
  background: var(--ota-elevated);
  border: 1px solid var(--ota-border);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: border-color var(--transition-fast);
}

.ota-source-card:hover { border-color: var(--ota-border-hover); }

.ota-source-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.ota-source-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--ota-text);
  flex: 1;
}

.ota-source-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.ota-source-type {
  font-size: 11px;
  color: var(--ota-text-muted);
}

.ota-source-relevance {
  font-size: 11px;
  color: var(--ota-text-muted);
}

.ota-source-claim { display: flex; flex-direction: column; gap: 4px; }

.ota-source-claim-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ota-gold);
}

.ota-source-claim-text {
  font-size: 12px;
  color: var(--ota-text-2);
  line-height: 1.5;
  margin: 0;
  font-style: italic;
}

/* ── Technical Tab ──────────────────────────────────── */
.ota-tech-tab {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ota-tech-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--ota-border);
}

.ota-tech-section:last-child { border-bottom: none; }

.ota-tech-section-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.10em;
  color: var(--ota-gold);
  margin: 0 0 6px;
}

.ota-tech-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 3px 0;
}

.ota-tech-label {
  font-size: 12px;
  color: var(--ota-text-muted);
  min-width: 140px;
  flex-shrink: 0;
}

.ota-tech-value {
  font-size: 12px;
  color: var(--ota-text);
  font-family: monospace;
  word-break: break-all;
}

.ota-tech-warnings {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 4px;
}

.ota-tech-warning {
  font-size: 12px;
  color: #fbbf24;
  padding: 4px 8px;
  background: rgba(245,158,11,0.08);
  border-radius: 6px;
  border-left: 2px solid var(--warning);
}

/* ── DB legacy selectors (keep for existing CSS class compat) ── */
.db-layout { display: flex; min-height: 100vh; }
.db-sidebar { width: var(--ota-sidebar-w); }

/* ── Responsive ─────────────────────────────────────── */
@media (max-width: 1280px) {
  .ota-three-panel-grid {
    grid-template-columns: 45% 1fr 1fr;
  }
}

@media (max-width: 1024px) {
  .ota-main-wrapper {
    margin-left: 0;
  }

  .ota-sidebar {
    transform: translateX(-100%);
    transition: transform var(--transition-base);
  }

  .ota-sidebar.open {
    transform: translateX(0);
  }

  .ota-three-panel-grid {
    grid-template-columns: 1fr;
    max-height: none;
  }

  .ota-panel {
    min-height: 360px;
    max-height: 480px;
    border-right: none;
    border-bottom: 1px solid var(--ota-border);
  }

  .ota-header-left {
    min-width: 0;
  }

  .ota-date-card {
    display: none;
  }
}

@media (max-width: 768px) {
  .ota-header {
    padding: 0 14px;
    gap: 10px;
  }

  .ota-header-center {
    max-width: none;
  }

  .ota-tab-content {
    padding: 14px;
  }

  .ota-info-row {
    grid-template-columns: 120px 1fr;
  }

  .ota-info-badges {
    grid-column: 2;
  }
}

@media (max-width: 480px) {
  .ota-upload-fields {
    flex-direction: column;
    min-width: 0;
  }

  .ota-three-panel-grid {
    grid-template-columns: 1fr;
  }
}
`;

css = css + newCss;
fs.writeFileSync(path, css, 'utf8');
console.log('OTA CSS classes appended successfully - ' + newCss.length + ' chars added');
