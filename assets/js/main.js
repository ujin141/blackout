/* ============================================================
   BLACKOUT — main.js
   Edit CONFIG below to point the site at your real accounts.
   ============================================================ */

const CONFIG = {
  instagram: 'blackoutcrew_official',          // handle without "@"
  email: 'ujin141@naver.com',                  // 지원서·문의가 도착하는 주소
  applySubject: 'BLACKOUT — Founding Member Application'
};

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const $  = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

/* ── language (ko default, en optional) ──────────────────── */
const LANG_KEY = 'blackout:lang';
let LANG = 'ko';

function splitLines() {
  $$('[data-reveal-lines]').forEach(h => {
    if (h.querySelector('.line')) {
      /* already split — rebuild from the current source text */
      h.innerHTML = [...h.querySelectorAll('.line > span')].map(s => s.innerHTML).join('<br>');
    }
    const parts = h.innerHTML.split(/<br\s*\/?>/i).map(s => s.trim()).filter(Boolean);
    h.innerHTML = parts.map(p => `<span class="line"><span>${p}</span></span>`).join('');
  });
}

function applyLang(next, { rebuild = true } = {}) {
  const dict = I18N[next];
  if (!dict) return;
  LANG = next;
  document.documentElement.lang = next;
  try { localStorage.setItem(LANG_KEY, next); } catch (e) { /* private mode */ }

  $$('[data-i18n]').forEach(el => {
    const v = dict[el.dataset.i18n];
    if (v == null) return;
    const attr = el.dataset.i18nAttr;
    if (attr) el.setAttribute(attr, v);
    else el.innerHTML = v;
  });

  document.title = dict['meta.title'] || document.title;
  localizeMembers();
  $$('.lang button').forEach(b => {
    const on = b.dataset.lang === next;
    b.classList.toggle('is-on', on);
    b.setAttribute('aria-pressed', String(on));
  });

  if (rebuild) splitLines();
}

(function initLang() {
  let saved = null;
  try { saved = localStorage.getItem(LANG_KEY); } catch (e) { /* ignore */ }
  const start = saved || 'ko';
  applyLang(start, { rebuild: false });
  $$('.lang button').forEach(b => {
    b.addEventListener('click', () => applyLang(b.dataset.lang));
  });
})();

/* ── contact details ─────────────────────────────────────── */
(function contactDetails() {
  const igUrl = `https://instagram.com/${CONFIG.instagram}`;
  const mailUrl = `mailto:${CONFIG.email}`;

  $$('[data-link="instagram"]').forEach(a => { a.href = igUrl; });
  $$('[data-link="email"]').forEach(a => { a.href = mailUrl; });
  $$('[data-text="instagram"]').forEach(el => { el.textContent = '@' + CONFIG.instagram; });
  $$('[data-text="email"]').forEach(el => { el.textContent = CONFIG.email; });

  const year = $('#year');
  if (year) year.textContent = new Date().getFullYear();
})();

/* ── members ─────────────────────────────────────────────── */
function pick(v) {
  if (v && typeof v === 'object') return v[LANG] ?? v.ko ?? v.en ?? '';
  return v || '';
}

function localizeMembers() {
  const dict = I18N[LANG] || I18N.ko;
  const list = typeof MEMBERS === 'undefined' ? [] : MEMBERS;

  $$('.member[data-index]').forEach(card => {
    const m = list[+card.dataset.index];
    if (!m) return;
    const role = card.querySelector('.member__role');
    const bio = card.querySelector('.member__bio');
    const genres = card.querySelector('.member__genres');
    const career = card.querySelector('.member__career');
    if (role) role.textContent = pick(m.role);
    if (bio) bio.textContent = pick(m.bio);
    if (genres) genres.textContent = (pick(m.genres) || []).join(' · ');
    if (career) {
      const items = pick(m.career) || [];
      career.replaceChildren(...items.map(c => {
        const li = document.createElement('li');
        li.textContent = c;
        return li;
      }));
    }
  });

  $$('.member--open').forEach(card => {
    card.querySelector('.member__name').textContent = dict['mem.open'];
    card.querySelector('.member__bio').textContent = dict['mem.opend'];
    card.querySelector('.member__apply').textContent = dict['mem.apply'];
  });
}

(function members() {
  const grid = document.getElementById('memberGrid');
  if (!grid) return;
  const list = typeof MEMBERS === 'undefined' ? [] : MEMBERS;
  const slots = typeof MEMBER_SLOTS === 'undefined' ? 0 : MEMBER_SLOTS;
  const dict = I18N[LANG] || I18N.ko;
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const html = [];

  list.forEach((m, i) => {
    /* photo = 카드를 꽉 채우는 사진, cutout = 생성된 조명 위에 올라가는 누끼 */
    const media = m.photo
      ? `<img src="${esc(m.photo)}" alt="${esc(m.name)}" loading="lazy" />`
      : m.cutout
        ? `<img class="member__cut" src="${esc(m.cutout)}" alt="${esc(m.name)}" loading="lazy" />`
        : '';
    const genres = pick(m.genres) || [];
    const genreHtml = genres.length
      ? `<p class="member__genres">${genres.map(esc).join(' · ')}</p>`
      : '';
    const career = pick(m.career) || [];
    const careerHtml = career.length
      ? `<ul class="member__career">${career.map(c => `<li>${esc(c)}</li>`).join('')}</ul>`
      : '';
    /* 값이 전체 URL이면 그대로, 아니면 핸들로 취급 */
    const url = (base, v) => v.includes('://') ? v : base + v;
    const links = [
      m.instagram && `<a href="${esc(url('https://instagram.com/', m.instagram))}" target="_blank" rel="noopener">@${esc(m.instagram)}</a>`,
      m.soundcloud && `<a href="${esc(url('https://soundcloud.com/', m.soundcloud))}" target="_blank" rel="noopener">SoundCloud</a>`
    ].filter(Boolean).join('');
    html.push(
      `<article class="member" data-reveal data-index="${i}">
         <div class="member__photo" ${m.photo ? '' : `data-art="${m.cutout ? 'stage' : 'portrait'}" data-seed="${i + 1}"`}>${media}</div>
         <div class="member__info">
           <h3 class="member__name">${esc(m.name)}</h3>
           <p class="member__role">${esc(pick(m.role))}</p>
           ${genreHtml}
           <p class="member__bio">${esc(pick(m.bio))}</p>
           ${careerHtml}
           ${links ? `<div class="member__links">${links}</div>` : ''}
         </div>
       </article>`
    );
  });

  for (let i = list.length; i < slots; i++) {
    html.push(
      `<article class="member member--open" data-reveal>
         <div class="member__photo member__photo--open"><span aria-hidden="true">+</span></div>
         <div class="member__info">
           <h3 class="member__name">${dict['mem.open']}</h3>
           <p class="member__role">0${i + 1}</p>
           <p class="member__bio">${dict['mem.opend']}</p>
           <button class="member__apply" type="button" data-open-apply>${dict['mem.apply']}</button>
         </div>
       </article>`
    );
  }

  grid.innerHTML = html.join('');
})();

/* ── intro ───────────────────────────────────────────────── */
(function intro() {
  const el = $('#intro');
  const bar = $('.intro__bar span');
  if (!el) return;

  const finish = () => {
    el.classList.add('is-done');
    document.body.classList.remove('is-locked');
    document.documentElement.classList.add('is-ready');
    setTimeout(() => el.remove(), 800);
  };

  if (reduceMotion) { finish(); return; }

  document.body.classList.add('is-locked');
  let p = 0;
  const tick = setInterval(() => {
    p = Math.min(100, p + 18 + Math.random() * 22);
    if (bar) bar.style.width = p + '%';
    if (p >= 100) { clearInterval(tick); setTimeout(finish, 260); }
  }, 170);
})();

/* ── nav ─────────────────────────────────────────────────── */
(function nav() {
  const bar = $('#nav');
  const burger = $('#burger');
  const menu = $('#menu');
  let last = 0;

  const onScroll = () => {
    const y = window.scrollY;
    bar.classList.toggle('is-stuck', y > 40);
    const open = menu.classList.contains('is-open');
    bar.classList.toggle('is-hidden', !open && y > 400 && y > last);
    last = y;
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  const setMenu = open => {
    burger.setAttribute('aria-expanded', String(open));
    burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    document.body.classList.toggle('is-locked', open);
    if (open) {
      menu.hidden = false;
      requestAnimationFrame(() => menu.classList.add('is-open'));
    } else {
      menu.classList.remove('is-open');
      setTimeout(() => { if (!menu.classList.contains('is-open')) menu.hidden = true; }, 350);
    }
  };

  burger.addEventListener('click', () => setMenu(burger.getAttribute('aria-expanded') !== 'true'));
  $$('#menu a').forEach(a => a.addEventListener('click', () => setMenu(false)));
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && burger.getAttribute('aria-expanded') === 'true') setMenu(false);
  });

  /* active link */
  const links = $$('.nav__links a');
  const sections = links
    .map(a => ({ a, el: $(a.getAttribute('href')) }))
    .filter(s => s.el);

  const spy = new IntersectionObserver(entries => {
    entries.forEach(en => {
      const hit = sections.find(s => s.el === en.target);
      if (hit && en.isIntersecting) {
        links.forEach(l => l.classList.remove('is-active'));
        hit.a.classList.add('is-active');
      }
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  sections.forEach(s => spy.observe(s.el));
})();

/* ── reveal on scroll ────────────────────────────────────── */
(function reveal() {
  splitLines();   /* headings become masked lines, one per <br> */

  const targets = $$('[data-reveal], [data-reveal-lines]');
  if (reduceMotion) { targets.forEach(t => t.classList.add('is-in')); return; }

  const io = new IntersectionObserver((entries, obs) => {
    entries.forEach(en => {
      if (!en.isIntersecting) return;
      en.target.classList.add('is-in');
      obs.unobserve(en.target);
    });
  }, { rootMargin: '0px 0px -12% 0px', threshold: 0.12 });

  /* stagger siblings inside the same grid/list */
  const groups = new Map();
  targets.forEach(t => {
    const key = t.parentElement;
    const arr = groups.get(key) || [];
    arr.push(t);
    groups.set(key, arr);
  });
  groups.forEach(arr => {
    if (arr.length < 2) return;
    arr.forEach((t, i) => { t.style.transitionDelay = Math.min(i * 0.07, 0.5) + 's'; });
  });

  targets.forEach(t => io.observe(t));
})();

/* ============================================================
   Visuals — generated on canvas (no stock photos).
   Swap any <figure class="tile"> content for a real
   <img> or <video> and it inherits the same treatment.
   ============================================================ */

const seeded = seed => () => {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
};

function fitCanvas(cv, cap = 2) {
  const r = cv.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, cap);
  const w = Math.max(1, Math.round(r.width * dpr));
  const h = Math.max(1, Math.round(r.height * dpr));
  if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
  return { w, h, dpr };
}

/* crowd of heads + shoulders along the bottom */
function drawCrowd(ctx, w, h, rng, baseline = 0.78, density = 34, headDiv = 26) {
  ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#000';
  for (let i = 0; i < density; i++) {
    const x = rng() * w * 1.1 - w * 0.05;
    const scale = 0.55 + rng() * 0.85;
    const rHead = (w / headDiv) * scale;
    const y = h * baseline + (rng() - 0.5) * h * 0.09 + rHead * 0.4;
    ctx.beginPath();
    ctx.arc(x, y, rHead, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(x, y + rHead * 2.1, rHead * 2.05, rHead * 1.9, 0, Math.PI, Math.PI * 2);
    ctx.fill();
    ctx.fillRect(x - rHead * 2.05, y + rHead * 2.1, rHead * 4.1, h);
  }
}

/* raised arms */
function drawHands(ctx, w, h, rng, count = 22, widthDiv = 90) {
  ctx.fillStyle = '#000';
  ctx.strokeStyle = '#000';
  ctx.lineCap = 'round';
  for (let i = 0; i < count; i++) {
    const x = rng() * w;
    const top = h * (0.3 + rng() * 0.35);
    const lw = (w / widthDiv) * (0.7 + rng() * 1.1);
    ctx.lineWidth = lw;
    ctx.beginPath();
    ctx.moveTo(x, h);
    ctx.quadraticCurveTo(x + (rng() - 0.5) * w * 0.06, (top + h) / 2, x + (rng() - 0.5) * w * 0.05, top);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(x + (rng() - 0.5) * w * 0.05, top, lw * 0.9, 0, Math.PI * 2);
    ctx.fill();
  }
}

function haze(ctx, w, h, x, y, r, a) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, `rgba(255,255,255,${a})`);
  g.addColorStop(0.4, `rgba(255,255,255,${a * 0.28})`);
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(x - r, y - r, r * 2, r * 2);
}

/* a light cone from an origin point */
function beam(ctx, ox, oy, angle, spread, len, a) {
  ctx.save();
  ctx.translate(ox, oy);
  ctx.rotate(angle);
  const g = ctx.createLinearGradient(0, 0, 0, len);
  g.addColorStop(0, `rgba(255,255,255,${a})`);
  g.addColorStop(0.35, `rgba(255,255,255,${a * 0.4})`);
  g.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = g;
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(-spread, len);
  ctx.lineTo(spread, len);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

/* raised arms rising out of the crowd line */
function armsAbove(ctx, w, h, rng, line, count, widthDiv) {
  ctx.save();
  ctx.translate(0, h * line);
  drawHands(ctx, w, h * (1 - line), rng, count, widthDiv);
  ctx.restore();
}

const ART = {
  beams(ctx, w, h, rng) {
    ctx.globalCompositeOperation = 'screen';
    for (let i = 0; i < 8; i++) {
      const ox = w * (0.1 + rng() * 0.8);
      beam(ctx, ox, -h * 0.05, (rng() - 0.5) * 0.6, w * (0.012 + rng() * 0.03), h * 1.2, 0.16 + rng() * 0.2);
    }
    haze(ctx, w, h, w * 0.5, h * 0.5, w * 0.55, 0.13);
    haze(ctx, w, h, w * 0.5, h * 0.86, w * 0.7, 0.1);
    ctx.globalCompositeOperation = 'source-over';
    armsAbove(ctx, w, h, rng, 0.78, Math.round(w / 70), 300);
    drawCrowd(ctx, w, h, rng, 0.86, Math.round(w / 22), 62);
  },
  crowd(ctx, w, h, rng) {
    ctx.globalCompositeOperation = 'screen';
    haze(ctx, w, h, w * 0.5, h * 0.34, w * 0.9, 0.26);
    for (let i = 0; i < 5; i++) {
      beam(ctx, w * (0.1 + i * 0.2), -h * 0.1, (rng() - 0.5) * 0.45, w * 0.022, h * 1.1, 0.12);
    }
    ctx.globalCompositeOperation = 'source-over';
    armsAbove(ctx, w, h, rng, 0.58, Math.round(w / 55), 240);
    drawCrowd(ctx, w, h, rng, 0.68, Math.round(w / 14), 48);
  },
  strobe(ctx, w, h, rng) {
    ctx.globalCompositeOperation = 'screen';
    const bars = 11;
    for (let i = 0; i < bars; i++) {
      const x = (i + 0.5) * (w / bars) + (rng() - 0.5) * 6;
      const bw = w / bars * (0.08 + rng() * 0.14);
      const g = ctx.createLinearGradient(x, 0, x, h);
      const a = 0.18 + rng() * 0.4;
      g.addColorStop(0, `rgba(255,255,255,${a})`);
      g.addColorStop(0.7, `rgba(255,255,255,${a * 0.18})`);
      g.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = g;
      ctx.fillRect(x - bw / 2, 0, bw, h);
    }
    haze(ctx, w, h, w * 0.5, h * 0.75, w * 0.6, 0.1);
    ctx.globalCompositeOperation = 'source-over';
    drawCrowd(ctx, w, h, rng, 0.82, Math.round(w / 26), 55);
  },
  smoke(ctx, w, h, rng) {
    ctx.globalCompositeOperation = 'screen';
    for (let i = 0; i < 18; i++) {
      haze(ctx, w, h, rng() * w, h * (0.2 + rng() * 0.7), w * (0.14 + rng() * 0.32), 0.05 + rng() * 0.06);
    }
    beam(ctx, w * 0.74, -h * 0.1, -0.38, w * 0.035, h * 1.25, 0.22);
    beam(ctx, w * 0.26, -h * 0.1, 0.3, w * 0.028, h * 1.25, 0.14);
    ctx.globalCompositeOperation = 'source-over';
    drawCrowd(ctx, w, h, rng, 0.92, Math.round(w / 40), 58);
  },
  lasers(ctx, w, h, rng) {
    ctx.globalCompositeOperation = 'screen';
    haze(ctx, w, h, w * 0.5, h * 0.05, w * 0.3, 0.22);
    ctx.lineCap = 'round';
    const ox = w * 0.5, oy = h * 0.03, len = h * 1.7;
    for (let i = 0; i < 40; i++) {
      const ang = ((i / 39) - 0.5) * 2.05 + (rng() - 0.5) * 0.03;
      ctx.strokeStyle = `rgba(255,255,255,${0.1 + rng() * 0.32})`;
      ctx.lineWidth = Math.max(1, w / 900);
      ctx.beginPath();
      ctx.moveTo(ox, oy);
      ctx.lineTo(ox + Math.sin(ang) * len, oy + Math.cos(ang) * len);
      ctx.stroke();
    }
    haze(ctx, w, h, w * 0.5, h * 0.6, w * 0.55, 0.07);
    ctx.globalCompositeOperation = 'source-over';
    armsAbove(ctx, w, h, rng, 0.82, Math.round(w / 80), 340);
    drawCrowd(ctx, w, h, rng, 0.9, Math.round(w / 22), 70);
  },
  booth(ctx, w, h, rng) {
    ctx.globalCompositeOperation = 'screen';
    haze(ctx, w, h, w * 0.5, h * 0.34, w * 0.7, 0.26);
    for (let i = 0; i < 3; i++) {
      beam(ctx, w * (0.25 + i * 0.25), -h * 0.05, (rng() - 0.5) * 0.35, w * 0.025, h * 1.1, 0.16);
    }
    ctx.globalCompositeOperation = 'source-over';
    /* booth block + figure behind the decks */
    ctx.fillStyle = '#000';
    const by = h * 0.7;
    const headR = Math.min(w, h) * 0.05;
    const cx = w * 0.5;
    ctx.beginPath(); ctx.arc(cx, by - headR * 3.2, headR, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath();
    ctx.ellipse(cx, by, headR * 2.1, headR * 2.6, 0, Math.PI, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#000';
    ctx.lineWidth = headR * 0.62;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(cx + headR * 0.9, by - headR * 1.9);
    ctx.lineTo(cx + headR * 2.7, by - headR * 0.5);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(cx - headR * 0.9, by - headR * 1.9);
    ctx.lineTo(cx - headR * 2.2, by - headR * 2.6);
    ctx.stroke();
    ctx.fillRect(w * 0.1, by, w * 0.8, h);
  },
  hands(ctx, w, h, rng) {
    ctx.globalCompositeOperation = 'screen';
    haze(ctx, w, h, w * 0.5, h * 0.3, w * 1.1, 0.3);
    for (let i = 0; i < 6; i++) {
      beam(ctx, w * (0.05 + i * 0.18), -h * 0.08, (rng() - 0.5) * 0.5, w * 0.03, h * 1.1, 0.12);
    }
    ctx.globalCompositeOperation = 'source-over';
    armsAbove(ctx, w, h, rng, 0.5, Math.round(w / 26), 130);
    drawCrowd(ctx, w, h, rng, 0.9, Math.round(w / 16), 40);
  },
  /* empty stage — goes behind a cut-out member so the person is the only figure */
  stage(ctx, w, h, rng) {
    ctx.globalCompositeOperation = 'screen';
    haze(ctx, w, h, w * 0.5, h * 0.3, w * 0.8, 0.3);
    const lean = (rng() - 0.5) * 0.4;
    beam(ctx, w * (0.24 + rng() * 0.12), -h * 0.06, lean + 0.24, w * 0.05, h * 1.2, 0.2);
    beam(ctx, w * (0.66 + rng() * 0.12), -h * 0.06, lean - 0.26, w * 0.045, h * 1.2, 0.17);
    beam(ctx, w * 0.5, -h * 0.06, lean, w * 0.03, h * 1.2, 0.1);
    for (let i = 0; i < 9; i++) {
      haze(ctx, w, h, rng() * w, h * (0.35 + rng() * 0.55), w * (0.18 + rng() * 0.3), 0.04);
    }
    /* floor bounce so the figure has something to stand on */
    const g = ctx.createLinearGradient(0, h, 0, h * 0.6);
    g.addColorStop(0, 'rgba(255,255,255,0.16)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, h * 0.6, w, h * 0.4);
    ctx.globalCompositeOperation = 'source-over';
  },

  /* backlit portrait — stands in for a member photo until a real one lands */
  portrait(ctx, w, h, rng) {
    ctx.globalCompositeOperation = 'screen';
    haze(ctx, w, h, w * 0.5, h * 0.34, w * 0.72, 0.24);
    const lean = (rng() - 0.5) * 0.5;
    beam(ctx, w * (0.3 + rng() * 0.4), -h * 0.06, lean, w * 0.05, h * 1.2, 0.16);
    beam(ctx, w * (0.2 + rng() * 0.6), -h * 0.06, lean - 0.5, w * 0.03, h * 1.2, 0.1);
    for (let i = 0; i < 8; i++) {
      haze(ctx, w, h, rng() * w, h * (0.4 + rng() * 0.5), w * (0.2 + rng() * 0.3), 0.035);
    }
    ctx.globalCompositeOperation = 'source-over';

    /* head + shoulders, slightly off-centre so no two cards match */
    const cx = w * (0.42 + rng() * 0.16);
    const r = Math.min(w, h) * (0.15 + rng() * 0.03);
    const shoulderY = h * (0.74 + rng() * 0.06);
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.arc(cx, shoulderY - r * 2.5, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(cx - r * 0.55, shoulderY - r * 1.6);
    ctx.lineTo(cx + r * 0.55, shoulderY - r * 1.6);
    ctx.lineTo(cx + r * 2.4, shoulderY + r * 0.6);
    ctx.quadraticCurveTo(cx + r * 2.7, shoulderY + r * 1.4, cx + r * 2.7, h);
    ctx.lineTo(cx - r * 2.7, h);
    ctx.quadraticCurveTo(cx - r * 2.7, shoulderY + r * 1.4, cx - r * 2.4, shoulderY + r * 0.6);
    ctx.closePath();
    ctx.fill();
  },
  silhouette(ctx, w, h, rng) {
    ctx.globalCompositeOperation = 'screen';
    const g = ctx.createLinearGradient(0, h * 0.72, 0, h * 0.25);
    g.addColorStop(0, 'rgba(255,255,255,0.4)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
    haze(ctx, w, h, w * 0.5, h * 0.72, w * 0.45, 0.2);
    ctx.globalCompositeOperation = 'source-over';
    armsAbove(ctx, w, h, rng, 0.66, Math.round(w / 60), 300);
    drawCrowd(ctx, w, h, rng, 0.78, Math.round(w / 14), 70);
  }
};

/* ── gallery tiles ───────────────────────────────────────── */
(function generatedArt() {
  const tiles = $$('[data-art]');
  if (!tiles.length) return;

  const paint = tile => {
    /* 꽉 채우는 사진·영상이 있으면 생성 아트는 건너뜀. 누끼(.member__cut)는 조명 위에 얹히므로 예외 */
    if (tile.querySelector('img:not(.member__cut), video')) return;
    let cv = tile.querySelector('canvas');
    if (!cv) {
      cv = document.createElement('canvas');
      tile.prepend(cv);
    }
    const { w, h } = fitCanvas(cv, 1.75);
    const ctx = cv.getContext('2d');
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#050505';
    ctx.fillRect(0, 0, w, h);
    const kind = tile.dataset.art;
    const seed = Number(tile.dataset.seed || 0);
    const rng = seeded(([...kind].reduce((a, c) => a + c.charCodeAt(0), 7) + seed * 131) * 977 + w);
    (ART[kind] || ART.beams)(ctx, w, h, rng);
    ctx.globalCompositeOperation = 'source-over';
  };

  const io = new IntersectionObserver((entries, obs) => {
    entries.forEach(en => {
      if (!en.isIntersecting) return;
      paint(en.target);
      obs.unobserve(en.target);
    });
  }, { rootMargin: '250px' });
  tiles.forEach(t => io.observe(t));

  let rt;
  window.addEventListener('resize', () => {
    clearTimeout(rt);
    rt = setTimeout(() => tiles.forEach(t => { if (t.querySelector('canvas')) paint(t); }), 220);
  });
})();

/* ── hero scene ──────────────────────────────────────────── */
(function heroScene() {
  const cv = $('#heroCanvas');
  if (!cv) return;
  const ctx = cv.getContext('2d');
  let w = 0, h = 0, raf = 0, t = 0, visible = true;

  const rng = seeded(20260731);
  const beams = Array.from({ length: 9 }, (_, i) => ({
    x: 0.08 + (i / 8) * 0.84,
    phase: rng() * Math.PI * 2,
    speed: 0.12 + rng() * 0.22,
    swing: 0.18 + rng() * 0.3,
    width: 0.018 + rng() * 0.035,
    alpha: 0.07 + rng() * 0.1
  }));
  const crowdSeed = Math.round(rng() * 1e6);

  let crowdLayer = null;
  const buildCrowd = () => {
    crowdLayer = document.createElement('canvas');
    crowdLayer.width = w; crowdLayer.height = h;
    const c = crowdLayer.getContext('2d');
    /* arms first, so heads sit in front of them */
    c.save();
    c.translate(0, h * 0.72);
    drawHands(c, w, h * 0.28, seeded(crowdSeed + 11), Math.round(w / 55), 340);
    c.restore();
    drawCrowd(c, w, h, seeded(crowdSeed), 0.92, Math.round(w / 30), 90);
  };

  const size = () => {
    const m = fitCanvas(cv, 1.6);
    w = m.w; h = m.h;
    buildCrowd();
  };

  const frame = () => {
    t += 0.0055;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, w, h);

    /* volumetric beams */
    ctx.globalCompositeOperation = 'screen';
    beams.forEach(b => {
      const a = Math.sin(t * b.speed * 6 + b.phase) * b.swing;
      const pulse = 0.72 + Math.sin(t * 2.4 + b.phase) * 0.28;
      beam(ctx, b.x * w, -h * 0.08, a, w * b.width, h * 1.25, b.alpha * pulse);
    });

    /* haze */
    haze(ctx, w, h, w * (0.5 + Math.sin(t * 0.7) * 0.12), h * 0.45, w * 0.55, 0.055);
    haze(ctx, w, h, w * (0.5 - Math.sin(t * 0.5) * 0.2), h * 0.7, w * 0.4, 0.04);

    /* floor bloom behind the crowd */
    const g = ctx.createLinearGradient(0, h * 0.95, 0, h * 0.55);
    g.addColorStop(0, `rgba(255,255,255,${0.1 + Math.sin(t * 1.6) * 0.03})`);
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, h * 0.5, w, h * 0.5);

    /* crowd silhouette */
    ctx.globalCompositeOperation = 'source-over';
    if (crowdLayer) ctx.drawImage(crowdLayer, 0, 0);

    raf = requestAnimationFrame(frame);
  };

  const start = () => { if (!raf && visible && !reduceMotion) raf = requestAnimationFrame(frame); };
  const stop = () => { cancelAnimationFrame(raf); raf = 0; };

  const still = () => {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, w, h);
    ctx.globalCompositeOperation = 'screen';
    beams.forEach(b => beam(ctx, b.x * w, -h * 0.08, (b.phase % 1 - 0.5) * b.swing, w * b.width, h * 1.25, b.alpha));
    haze(ctx, w, h, w * 0.5, h * 0.45, w * 0.55, 0.06);
    ctx.globalCompositeOperation = 'source-over';
    if (crowdLayer) ctx.drawImage(crowdLayer, 0, 0);
  };

  size();
  if (reduceMotion) still(); else start();

  let rt;
  window.addEventListener('resize', () => {
    clearTimeout(rt);
    rt = setTimeout(() => { size(); if (reduceMotion) still(); }, 200);
  });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop(); else start();
  });

  new IntersectionObserver(([en]) => {
    visible = en.isIntersecting;
    visible ? start() : stop();
  }, { threshold: 0.02 }).observe(cv);
})();

/* ── 3D logo ─────────────────────────────────────────────── */
(function logo3d() {
  const el = $('#logo3d');
  if (!el) return;

  const MAX = 16;          /* degrees of tilt at the far edge */
  const fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  let raf = 0, target = null, lift = 0, pointerIn = false;

  const set = (rx, ry, mx, my) => {
    el.style.setProperty('--rx', rx.toFixed(2) + 'deg');
    el.style.setProperty('--ry', ry.toFixed(2) + 'deg');
    el.style.setProperty('--mx', mx.toFixed(1) + '%');
    el.style.setProperty('--my', my.toFixed(1) + '%');
  };

  const frame = () => {
    raf = 0;
    if (!target) return;
    const { x, y } = target;
    set(-y * MAX, x * MAX, (x * 0.5 + 0.5) * 100, (y * 0.5 + 0.5) * 100);
  };

  /* the whole hero reacts, so the logo turns towards you before you reach it */
  const zone = $('.hero') || el;

  const onMove = e => {
    if (!fine || reduceMotion) return;
    const r = el.getBoundingClientRect();
    const cx = r.left + r.width / 2;
    const cy = r.top + r.height / 2;
    /* normalised distance from the logo centre, softened outside its box */
    const x = Math.max(-1, Math.min(1, (e.clientX - cx) / (r.width * 0.9)));
    const y = Math.max(-1, Math.min(1, (e.clientY - cy) / (r.height * 0.9)));
    pointerIn = true;
    target = { x, y };
    if (!raf) raf = requestAnimationFrame(frame);
  };

  const setLift = v => {
    if (lift === v) return;
    lift = v;
    el.style.setProperty('--lift', v);
  };

  zone.addEventListener('pointermove', onMove, { passive: true });
  zone.addEventListener('pointerleave', () => {
    pointerIn = false;
    target = null;
    setLift(0);
    el.classList.remove('is-tracking');
  });

  el.addEventListener('pointerenter', () => {
    if (!fine || reduceMotion) return;
    setLift(1);
    el.classList.add('is-tracking', 'is-surging');
    setTimeout(() => el.classList.remove('is-surging'), 600);
  });
  el.addEventListener('pointerleave', () => {
    setLift(0);
    el.classList.remove('is-tracking');
  });

  /* touch: a tap still fires the surge + bloom */
  el.addEventListener('touchstart', () => {
    setLift(1);
    el.classList.add('is-surging');
    setTimeout(() => { el.classList.remove('is-surging'); setLift(0); }, 900);
  }, { passive: true });

  /* gentle idle drift so it never looks like a flat sticker */
  if (!reduceMotion) {
    let t = 0, visible = true;
    const idle = () => {
      if (!pointerIn && visible) {
        t += 0.006;
        set(Math.sin(t * 0.9) * 2.2, Math.cos(t * 0.7) * 3.2, 50, 40);
      }
      requestAnimationFrame(idle);
    };
    new IntersectionObserver(([en]) => { visible = en.isIntersecting; }, { threshold: 0.05 }).observe(el);
    requestAnimationFrame(idle);
  }
})();

/* ── apply modal ─────────────────────────────────────────── */
(function apply() {
  const modal = $('#apply');
  const form = $('#applyForm');
  const err = $('#formError');
  if (!modal || !form) return;
  let opener = null;

  const open = e => {
    opener = e?.currentTarget || null;
    modal.hidden = false;
    document.body.classList.add('is-locked');
    requestAnimationFrame(() => {
      modal.classList.add('is-open');
      $('#f-name').focus({ preventScroll: true });
    });
  };
  const close = () => {
    modal.classList.remove('is-open');
    document.body.classList.remove('is-locked');
    setTimeout(() => { modal.hidden = true; }, 400);
    opener?.focus({ preventScroll: true });
  };

  $$('[data-open-apply]').forEach(b => b.addEventListener('click', open));
  $$('[data-close-apply]').forEach(b => b.addEventListener('click', close));
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && !modal.hidden) close();
  });

  /* keep tab focus inside the dialog */
  modal.addEventListener('keydown', e => {
    if (e.key !== 'Tab') return;
    const f = $$('button, input, select, textarea, a[href]', modal).filter(el => el.offsetParent !== null);
    if (!f.length) return;
    const first = f[0], lastEl = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); lastEl.focus(); }
    else if (!e.shiftKey && document.activeElement === lastEl) { e.preventDefault(); first.focus(); }
  });

  form.addEventListener('submit', e => {
    e.preventDefault();
    const d = new FormData(form);
    const name = (d.get('name') || '').toString().trim();
    const email = (d.get('email') || '').toString().trim();
    const role = (d.get('role') || '').toString().trim();

    const t = k => (I18N[LANG] || I18N.ko)[k];

    if (!name || !email || !role) {
      err.textContent = t('apply.err1');
      err.hidden = false;
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
      err.textContent = t('apply.err2');
      err.hidden = false;
      return;
    }
    err.hidden = true;

    const body = [
      `Name: ${name}`,
      `Email: ${email}`,
      `Role: ${role}`,
      `Link: ${(d.get('link') || '—').toString().trim() || '—'}`,
      '',
      'About:',
      (d.get('about') || '—').toString().trim() || '—',
      '',
      '— sent from blackout landing page'
    ].join('\n');

    const href = `mailto:${CONFIG.email}?subject=${encodeURIComponent(CONFIG.applySubject + ' — ' + role + ' / ' + name)}&body=${encodeURIComponent(body)}`;
    window.location.href = href;
  });
})();
