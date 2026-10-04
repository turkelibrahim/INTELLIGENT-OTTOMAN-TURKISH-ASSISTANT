import os

css_path = r"c:\Users\ibrah\OneDrive\Masaüstü\INTELLIGENT OTTOMAN TURKISH ASSISTANT\frontend\src\app\globals.css"

new_css = """
/* =====================================================
   AUTH REFERENCE MATCH - LOGIN / REGISTER
   ===================================================== */

.auth-page {
  height: 100vh;
  max-height: 100vh;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at center, #11141a 0%, #06080a 100%);
  color: #fff;
  font-family: var(--font-inter), sans-serif;
}

/* Background elements */
.auth-bg-ambient {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 30% 50%, rgba(217, 160, 91, 0.08) 0%, transparent 40%),
              radial-gradient(circle at 70% 50%, rgba(217, 160, 91, 0.05) 0%, transparent 40%);
  z-index: 0;
  pointer-events: none;
}

.auth-particles {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(217, 160, 91, 0.4) 1px, transparent 1px);
  background-size: 60px 60px;
  background-position: 0 0, 30px 30px;
  opacity: 0.1;
  z-index: 0;
  pointer-events: none;
}

/* Left Document */
.auth-document-wrapper {
  position: absolute;
  left: -5vw;
  top: 15vh;
  width: 45vw;
  height: 70vh;
  z-index: 1;
  transform: rotate(-10deg);
  opacity: 0.9;
  pointer-events: none;
}

.auth-image-left {
  object-fit: contain;
  object-position: left center;
  filter: drop-shadow(0 0 30px rgba(217, 160, 91, 0.15));
}

.auth-ai-medallion {
  position: absolute;
  bottom: 50px;
  right: 120px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: 1px solid rgba(217, 160, 91, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: serif;
  font-size: 24px;
  color: #d9a05b;
  background: rgba(10, 10, 10, 0.8);
  box-shadow: 0 0 20px rgba(217, 160, 91, 0.3);
}

/* Right Mosque */
.auth-mosque-wrapper {
  position: absolute;
  right: -5vw;
  bottom: 0;
  width: 50vw;
  height: 60vh;
  z-index: 1;
  opacity: 0.6;
  pointer-events: none;
}

.auth-image-right {
  object-fit: cover;
  object-position: right bottom;
}

/* Floral Corner */
.auth-floral-wrapper {
  position: absolute;
  right: 0;
  top: 0;
  width: 300px;
  height: 300px;
  z-index: 1;
  pointer-events: none;
}

.auth-image-corner {
  object-fit: contain;
  object-position: top right;
  opacity: 0.3;
}

/* Main Auth Stage */
.auth-stage {
  position: relative;
  z-index: 10;
  width: min(100%, 460px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

/* Brand */
.auth-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 8px;
}

.auth-tughra-wrapper {
  position: relative;
  width: 100px;
  height: 100px;
  margin-bottom: 8px;
}

.auth-tughra-img {
  object-fit: contain;
  mix-blend-mode: screen;
}

.auth-brand-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #d9a05b;
}

.brand-line-1 {
  font-size: 14px;
  letter-spacing: 2px;
  font-weight: 300;
  color: rgba(255, 255, 255, 0.8);
}

.brand-line-2 {
  font-size: 24px;
  letter-spacing: 1px;
  font-family: serif;
  font-weight: 600;
}

.brand-line-3 {
  font-size: 12px;
  letter-spacing: 3px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-style: normal;
  color: rgba(255, 255, 255, 0.6);
}

.brand-dash {
  width: 20px;
  height: 1px;
  background: rgba(217, 160, 91, 0.5);
}

/* Card */
.auth-card {
  background: rgba(15, 18, 22, 0.7);
  border: 1px solid rgba(217, 160, 91, 0.2);
  border-radius: 12px;
  padding: 32px;
  width: 100%;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.auth-card-header {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.auth-card-header h1 {
  font-size: 32px;
  font-family: serif;
  color: #fff;
  margin: 0;
  font-weight: 500;
}

.auth-ornament {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  justify-content: center;
  margin: 8px 0;
}

.auth-ornament::before,
.auth-ornament::after {
  content: "";
  height: 1px;
  width: 40px;
  background: linear-gradient(90deg, transparent, rgba(217, 160, 91, 0.6), transparent);
}

.auth-ornament-diamond {
  width: 6px;
  height: 6px;
  background: #d9a05b;
  transform: rotate(45deg);
}

.auth-card-header p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

/* Forms */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.auth-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
}

.auth-field > span {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.auth-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.auth-input-wrap svg:first-child {
  position: absolute;
  left: 12px;
  width: 18px;
  height: 18px;
  color: rgba(255, 255, 255, 0.4);
  pointer-events: none;
}

.auth-input-wrap input {
  width: 100%;
  height: 48px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0 40px;
  color: #fff;
  font-size: 15px;
  transition: border-color 0.2s;
}

.auth-input-wrap input:focus {
  outline: none;
  border-color: #d9a05b;
}

.auth-eye {
  position: absolute;
  right: 12px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.4);
  padding: 4px;
}

.auth-eye:hover, .auth-eye.active {
  color: #d9a05b;
}

.auth-eye svg {
  width: 18px;
  height: 18px;
}

.auth-form-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.auth-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
}

.auth-checkbox input {
  display: none;
}

.auth-checkbox span {
  width: 18px;
  height: 18px;
  border: 1px solid rgba(217, 160, 91, 0.6);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-checkbox input:checked + span::after {
  content: "✓";
  color: #d9a05b;
  font-size: 14px;
}

.auth-forgot {
  color: #d9a05b;
  text-decoration: none;
}

.auth-forgot:hover {
  text-decoration: underline;
}

.auth-submit {
  height: 48px;
  background: linear-gradient(135deg, #dfa968, #b07e3a);
  border: none;
  border-radius: 8px;
  color: #111;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  margin-top: 8px;
}

.auth-submit:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(217, 160, 91, 0.4);
}

.auth-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: -8px 0;
}

.auth-divider::before,
.auth-divider::after {
  content: "";
  height: 1px;
  width: 60px;
  background: rgba(217, 160, 91, 0.2);
}

.auth-switch {
  text-align: center;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.auth-switch a {
  color: #d9a05b;
  text-decoration: none;
  font-weight: 500;
  margin-left: 4px;
}

.auth-switch a:hover {
  text-decoration: underline;
}

/* Footer */
.auth-footer {
  position: absolute;
  bottom: 24px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  z-index: 10;
}

.auth-trust-row {
  display: flex;
  gap: 32px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
}

.auth-trust-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.auth-trust-icon {
  color: #d9a05b;
}

.auth-footer small {
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
}

/* Media Queries */
@media (max-width: 1024px) {
  .auth-document-wrapper, .auth-mosque-wrapper, .auth-floral-wrapper {
    opacity: 0.3;
  }
}

@media (max-width: 768px) {
  .auth-page {
    padding: 24px;
    height: auto;
    min-height: 100vh;
    overflow-y: auto;
    justify-content: flex-start;
  }
  .auth-stage {
    margin-top: 40px;
    margin-bottom: 80px;
  }
  .auth-footer {
    position: relative;
    bottom: 0;
  }
  .auth-trust-row {
    flex-direction: column;
    gap: 16px;
    align-items: center;
  }
}
"""

with open(css_path, "a", encoding="utf-8") as f:
    f.write("\n" + new_css)
