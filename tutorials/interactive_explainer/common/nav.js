/* ═══════════════════════════════════════════════════════════════════════════
   UGP Physics — Interactive Explainer
   nav.js — Keyboard navigation
   ═══════════════════════════════════════════════════════════════════════════ */

'use strict';

function initNav() {
  const prevLink = document.querySelector('.nav-btn--prev');
  const nextLink = document.querySelector('.nav-btn--next');
  if (!prevLink && !nextLink) return;

  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;

    if (e.key === 'ArrowLeft'  && prevLink) { e.preventDefault(); window.location.href = prevLink.href; }
    if (e.key === 'ArrowRight' && nextLink) { e.preventDefault(); window.location.href = nextLink.href; }
  });
}

document.addEventListener('DOMContentLoaded', initNav);
