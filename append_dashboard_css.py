import os

css_path = r"c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT\frontend\src\app\globals.css"

new_css = """
/* =====================================================
   DASHBOARD UI 
   ===================================================== */
:root {
  --bg-primary: #06141c;
  --bg-secondary: #091b24;
  --bg-card: #0b2029;
  --bg-card-hover: #102a34;
  --gold-primary: #d9a441;
  --gold-light: #f0c56b;
  --gold-muted: #92713b;
  --text-primary: #f2eee4;
  --text-secondary: #aeb9bb;
  --text-muted: #77878a;
  --border-primary: rgba(217,164,65,0.35);
  --border-soft: rgba(255,255,255,0.08);
}

.db-layout {
  display: flex;
  height: 100vh;
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-inter), sans-serif;
  overflow: hidden;
}

/* Sidebar */
.db-sidebar {
  width: 260px;
  background-color: var(--bg-secondary);
  border-right: 1px solid var(--border-soft);
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 100;
}

.db-sidebar-logo {
  display: flex;
  align-items: center;
  padding: 24px;
  gap: 16px;
  border-bottom: 1px solid var(--border-soft);
}

.db-logo-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.db-logo-text {
  display: flex;
  flex-direction: column;
}

.db-logo-main {
  font-family: serif;
  font-size: 16px;
  color: var(--gold-primary);
  letter-spacing: 1px;
}

.db-logo-sub {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 2px;
}

.db-sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: 16px 12px;
  gap: 8px;
  flex: 1;
}

.db-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.2s;
  position: relative;
}

.db-nav-item:hover {
  background-color: var(--bg-card-hover);
  color: var(--text-primary);
}

.db-nav-item.active {
  background-color: rgba(30, 80, 100, 0.4);
  color: var(--gold-primary);
}

.db-nav-item.active::before {
  content: "";
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  height: 24px;
  width: 3px;
  background-color: var(--gold-primary);
  border-radius: 0 4px 4px 0;
}

/* Main Wrapper */
.db-main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-image: 
    url('/auth/mosque-silhouette.png'),
    url('/auth/floral-pattern.png');
  background-position: bottom right, top right;
  background-repeat: no-repeat;
  background-size: 40%, 20%;
  background-blend-mode: overlay;
  position: relative;
}

.db-main-wrapper::before {
  content: "";
  position: absolute;
  inset: 0;
  background: var(--bg-primary);
  opacity: 0.95;
  z-index: 0;
}

/* Header */
.db-header {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  border-bottom: 1px solid var(--border-primary);
  position: relative;
  z-index: 10;
  background: rgba(9, 27, 36, 0.8);
  backdrop-filter: blur(10px);
}

.db-header-title {
  font-family: serif;
  font-size: 20px;
  color: var(--gold-primary);
  margin: 0;
  font-weight: 500;
}

.db-header-center {
  flex: 1;
  max-width: 400px;
  margin: 0 32px;
}

.db-search-form {
  position: relative;
  display: flex;
  align-items: center;
}

.db-search-input {
  width: 100%;
  height: 40px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-soft);
  border-radius: 20px;
  padding: 0 16px 0 40px;
  color: var(--text-primary);
  font-size: 14px;
}

.db-search-input:focus {
  outline: none;
  border-color: var(--gold-muted);
}

.db-search-btn {
  position: absolute;
  left: 12px;
  background: none;
  border: none;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
}

.db-header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.db-date-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  padding: 8px 16px;
}

.db-date-icon {
  color: var(--gold-primary);
}

.db-date-info {
  display: flex;
  flex-direction: column;
}

.db-date-hijri {
  font-family: serif;
  color: var(--gold-primary);
  font-size: 13px;
}

.db-date-gregorian {
  font-size: 11px;
  color: var(--text-secondary);
}

.db-date-weather {
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
}

.db-icon-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: color 0.2s;
}

.db-icon-btn:hover {
  color: var(--gold-primary);
}

.notification-dot {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 14px;
  height: 14px;
  background: var(--gold-primary);
  color: var(--bg-primary);
  font-size: 9px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

/* Content Area */
.db-content-area {
  flex: 1;
  position: relative;
  z-index: 10;
  padding: 24px;
  overflow-y: auto;
}

/* Workspace */
.db-workspace {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 24px;
}

.db-workspace-main-panels {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  flex: 1;
  min-height: 500px;
}

/* Panels */
.db-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.db-panel-header {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px dashed var(--border-primary);
  background: rgba(0, 0, 0, 0.2);
}

.db-panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: serif;
  font-size: 16px;
  color: var(--gold-primary);
  margin: 0;
}

.db-panel-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  position: relative;
}

.db-panel-footer {
  padding: 12px 16px;
  border-top: 1px dashed var(--border-primary);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(0, 0, 0, 0.2);
}

/* Panel internals */
.document-viewer-content {
  padding: 0 !important;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
}

.document-stage-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.document-image-stage {
  position: relative;
}

.document-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.viewer-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px !important;
}

.zoom-controls, .action-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.zoom-controls button, .action-controls button {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid var(--border-soft);
  color: var(--text-primary);
  width: 32px;
  height: 32px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.zoom-controls button:hover, .action-controls button:hover {
  border-color: var(--gold-muted);
  color: var(--gold-primary);
}

.db-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
  text-align: center;
  gap: 16px;
}

.db-text-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.db-text-line {
  padding: 4px 8px;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  transition: background 0.2s;
  cursor: pointer;
}

.db-text-line:hover {
  background: rgba(255, 255, 255, 0.05);
}

.db-text-line.active {
  background: rgba(217, 164, 65, 0.15);
}

.db-line-text {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-primary);
}

.arabic-cell, [dir="rtl"] {
  font-family: serif;
  font-size: 18px;
}

.db-line-confidence {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 12px;
  height: fit-content;
}

.db-line-confidence.high { background: rgba(46, 216, 182, 0.2); color: #2ed8b6; }
.db-line-confidence.medium { background: rgba(244, 200, 77, 0.2); color: #f4c84d; }
.db-line-confidence.low { background: rgba(255, 145, 77, 0.2); color: #ff914d; }

.db-editor-textarea {
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.3);
  border: 1px solid var(--gold-muted);
  color: #fff;
  padding: 12px;
  resize: none;
  border-radius: 4px;
  font-family: inherit;
  font-size: 15px;
}
.db-editor-textarea:focus {
  outline: none;
  border-color: var(--gold-primary);
}

.db-confidence-indicator {
  font-size: 13px;
  color: var(--gold-primary);
}

.db-action-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-primary);
  color: var(--gold-primary);
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.db-action-btn:hover {
  background: var(--gold-primary);
  color: var(--bg-primary);
}

.db-primary-btn {
  background: var(--gold-primary);
  border: 1px solid var(--gold-light);
  color: var(--bg-primary);
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
}

.db-primary-btn:hover {
  background: var(--gold-light);
}

.db-text-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 6px 12px;
}
.db-text-btn:hover {
  color: var(--text-primary);
}

/* Transliteration Bottom Panel */
.db-panel-bottom {
  background: var(--bg-card);
  border: 1px solid var(--border-primary);
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  transition: max-height 0.3s ease;
}

.db-panel-bottom.open {
  max-height: 300px;
}

.db-panel-bottom.closed {
  max-height: 48px; /* just header */
}

/* Responsive */
@media (max-width: 1024px) {
  .db-workspace-main-panels {
    grid-template-columns: 1fr;
    height: auto;
  }
  .db-panel {
    min-height: 400px;
  }
  .db-sidebar {
    width: 60px;
  }
  .db-logo-text, .db-nav-label {
    display: none;
  }
}
"""

with open(css_path, "a", encoding="utf-8") as f:
    f.write("\n" + new_css)
