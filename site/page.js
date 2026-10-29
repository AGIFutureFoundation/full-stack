(() => {
  "use strict";
  const D = JSON.parse(document.getElementById("spec").textContent);
  const S = D.spec, P = D.plan, T = S.target, E = S.event;
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduce) document.documentElement.classList.add("motion");
  const NS = "http://www.w3.org/2000/svg";
  // SVG presentation attributes can't take var(), so those go through style
  const el = (tag, attrs = {}, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) {
      const v = String(attrs[k]);
      if (v.startsWith("var(")) e.style.setProperty(k, v); else e.setAttribute(k, v);
    }
    if (parent) parent.appendChild(e);
    return e;
  };
  const fmt = (n, d = 1) => n.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
  const label = k => k.replace(/_/g, " ").replace(/^./, c => c.toUpperCase());
  const TONE = { base: ["var(--pink-30)", "var(--pink-20)"], body: ["var(--purple-30)", "var(--purple-20)"], top: ["var(--yellow-30)", "var(--yellow-20)"] };
  const cakeSwatch = name => `<svg class="sw" aria-hidden="true" style="--cake-top:${TONE[name][0]};--cake-side:${TONE[name][1]}"><use href="#cake" width="100%" height="100%"/></svg>`;

  /* one polite status line for screen readers; everything else stays quiet */
  const status = $("#sr-status");
  let sayTimer;
  const say = (msg, delay = 0) => {
    clearTimeout(sayTimer);
    status.textContent = "";
    sayTimer = setTimeout(() => { status.textContent = msg; }, Math.max(delay, 60));
  };
  const toastEl = $("#toast");
  let toastTimer;
  const toast = msg => {
    toastEl.textContent = msg;
    toastEl.hidden = false;
    say(msg);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toastEl.hidden = true; }, 2400);
  };

  /* ---------- nav: phones get a sticky bar that compacts, everyone narrow gets the menu ---------- */
  const nav = $("#nav"), menu = $("#menu"), burger = $(".burger");
  const phone = matchMedia("(max-width: 767px)");
  let compact = false;
  const onScroll = () => {
    const y = scrollY;
    if (!compact && y > 24) compact = true;
    else if (compact && y < 8) compact = false;
    nav.classList.toggle("is-scrolled", compact && phone.matches);
  };
  addEventListener("scroll", onScroll, { passive: true });
  phone.addEventListener("change", onScroll);
  onScroll();

  if (typeof menu.showModal === "function") {
    burger.addEventListener("click", () => { menu.showModal(); burger.setAttribute("aria-expanded", "true"); });
    $(".menu-close").addEventListener("click", () => menu.close());
    menu.addEventListener("close", () => burger.setAttribute("aria-expanded", "false"));
    menu.addEventListener("click", e => {
      const a = e.target.closest('a[href^="#"]');
      if (!a) return;
      e.preventDefault();
      menu.close();
      const target = document.querySelector(a.hash);
      if (!target) return;
      // wait for the scroll lock to lift, or the smooth scroll is cancelled
      requestAnimationFrame(() => requestAnimationFrame(() => {
        target.scrollIntoView({ behavior: reduce ? "auto" : "smooth" });
        const h = target.querySelector("h2") || target;
        h.setAttribute("tabindex", "-1");
        h.focus({ preventScroll: true });
        history.replaceState(null, "", a.hash);
      }));
    });
    matchMedia("(max-width: 960px)").addEventListener("change", e => { if (!e.matches && menu.open) menu.close(); });
  } else {
    burger.addEventListener("click", () => { location.hash = "#why"; });
  }

  /* ---------- countdown, then "live", then the past tense ---------- */
  const start = new Date(E.start).getTime();
  const liveMs = E.live_hours * 36e5;
  const cd = $("#countdown");
  const day = E.date.replace(/,\s*\d{4}$/, "");
  let timer;
  const tick = () => {
    const now = Date.now(), ms = start - now;
    if (ms > 0) {
      const d = Math.floor(ms / 864e5), h = Math.floor(ms / 36e5) % 24, m = Math.floor(ms / 6e4) % 60;
      cd.textContent = `Attempt in ${d ? d + "d " : ""}${h}h ${String(m).padStart(2, "0")}m · ${E.place}`;
    } else if (now - start < liveMs) {
      cd.textContent = `Live now · ${E.place}`;
      cd.dataset.live = "";
    } else {
      delete cd.dataset.live;
      cd.textContent = `Attempted ${day} · results in the test log`;
      const lede = $("#lede");
      if (lede.dataset.past) lede.textContent = lede.dataset.past;
      clearInterval(timer);
    }
  };
  tick();
  timer = setInterval(tick, 30e3);

  /* ---------- buttons: the pancake.ai flood ---------- */
  const FILLS = ["var(--yellow-30)", "var(--purple-30)", "var(--green-20)"];
  const startFill = s => { let h = 0; for (const ch of s) h = (h * 31 + ch.charCodeAt(0)) >>> 0; return h % FILLS.length; };
  if (!reduce) $$(".button").forEach(b => {
    const lbl = document.createElement("span"), l1 = document.createElement("span");
    lbl.className = "lbl";
    l1.append(...b.childNodes);
    const l2 = l1.cloneNode(true);
    l2.setAttribute("aria-hidden", "true");
    lbl.append(l1, l2);
    const fx = document.createElement("span"), c = document.createElement("i");
    fx.className = "fx";
    fx.setAttribute("aria-hidden", "true");
    fx.append(c);
    b.append(fx, lbl);
    let n = startFill(l1.textContent.trim());
    const place = e => {
      const r = b.getBoundingClientRect(), d = Math.max(r.width, r.height) * 2.35;
      Object.assign(c.style, { width: `${d}px`, height: `${d}px`, left: `${e.clientX - r.left}px`, top: `${e.clientY - r.top}px` });
    };
    b.addEventListener("pointerenter", e => {
      if (e.pointerType === "touch") return;
      c.style.transition = "none";
      place(e);
      const fill = FILLS[n++ % FILLS.length];
      c.style.background = fill;
      b.style.setProperty("--fx-fill", fill);
      void c.offsetWidth;
      c.style.transition = "";
      c.style.transform = "translate(-50%,-50%) scale(1)";
      b.classList.add("is-fx");
    });
    b.addEventListener("pointerleave", e => {
      if (e.pointerType === "touch") return;
      place(e);
      c.style.transform = "translate(-50%,-50%) scale(0)";
      b.classList.remove("is-fx");
    });
  });
  document.addEventListener("touchstart", () => {}, { passive: true }); // lets iOS show :active

  /* ---------- the live tower, to scale ---------- */
  const tower = $("#tower-live");
  const base = 520, scale = 10, cx = 250, rx = 132;
  const layer = P.thickness_in * (1 - T.settle_ratio) * scale;
  const ruler = el("g", { opacity: .6 }, tower);
  el("line", { x1: rx, x2: rx, y1: base, y2: base - 48 * scale, stroke: "currentColor", "stroke-width": 1.5 }, ruler);
  for (let i = 0; i <= 48; i += 6) {
    el("line", { x1: rx - 8, x2: rx, y1: base - i * scale, y2: base - i * scale, stroke: "currentColor", "stroke-width": 1.5 }, ruler);
    el("text", { x: rx - 14, y: base - i * scale + 4, "text-anchor": "end", "font-family": "Geist, sans-serif", "font-size": 12, fill: "currentColor" }, ruler).textContent = i;
  }
  const cakesG = el("g", {}, tower);
  const groups = [];
  let y = base, count = 0, g;
  for (const z of P.sizes) {
    let n = z.in_tower;
    if (z.name === "top") n = Math.min(n, Math.round((T.build_to_in * scale - (base - y)) / layer));
    const w = z.ring_in * scale;
    for (let i = 0; i < n; i++) {
      if (count % 10 === 0) { g = el("g", { class: "tg" }, cakesG); groups.push({ g, n: 0, h: 0 }); }
      y -= layer;
      el("rect", { x: cx - w / 2, y, width: w, height: layer + .35, rx: 1.5, fill: i % 10 === 9 ? TONE[z.name][1] : TONE[z.name][0] }, g);
      count++;
      const last = groups[groups.length - 1];
      last.n = count;
      last.h = (base - y) / scale;
    }
  }
  el("rect", { x: cx - 80, y: base, width: 236, height: 7, rx: 3.5, fill: "currentColor" }, tower);
  for (const [v, c, name] of [[T.record_height_in, "var(--pink-40)", "record"], [T.build_to_in, "currentColor", "stop line"]]) {
    const yy = base - v * scale, below = name === "record";
    el("line", { x1: rx, x2: cx + 60, y1: yy, y2: yy, stroke: c, "stroke-width": 2, "stroke-dasharray": "6 5" }, tower);
    el("text", { x: cx + 66, y: yy + (below ? 16 : -4), "font-family": "Geist, sans-serif", "font-size": 14, "font-weight": 700, fill: "currentColor" }, tower).textContent = `${v} in`;
    el("text", { x: cx + 66, y: yy + (below ? 32 : 12), "font-family": "Geist, sans-serif", "font-size": 12, fill: "currentColor", opacity: .75 }, tower).textContent = name;
  }
  const mascot = el("use", { href: "#mascot", x: cx + 52, y: base - 89, width: 88, height: 89, class: "mascot" }, tower);
  mascot.style.transformOrigin = `${cx + 96}px ${base}px`;
  const roH = $("#ro-h"), roN = $("#ro-n"), stackBtn = $("#stack-btn");
  const readout = k => {
    const grp = k ? groups[k - 1] : null;
    roN.textContent = grp ? grp.n : 0;
    roH.textContent = fmt(grp ? grp.h : 0);
  };
  readout(groups.length);
  let building = false;
  const build = () => {
    if (building) return;
    if (reduce) { readout(groups.length); return; }
    building = true;
    stackBtn.setAttribute("aria-disabled", "true");
    tower.setAttribute("aria-busy", "true");
    const step = Math.min(110, 2800 / groups.length), t0 = performance.now();
    groups.forEach(({ g }, i) => g.animate(
      [{ opacity: 0, transform: "translateY(-22px)" }, { opacity: 1, transform: "none" }],
      { duration: 420, delay: i * step, easing: "cubic-bezier(.25,1.38,.42,1)", fill: "backwards" }));
    const total = groups.length * step;
    mascot.animate([{ opacity: 0, transform: "translateY(26px) scale(.7)" }, { opacity: 1, transform: "none" }],
      { duration: 600, delay: total, easing: "cubic-bezier(.3,1.6,.5,1)", fill: "backwards" });
    const frame = now => {
      const k = Math.min(groups.length, Math.floor((now - t0) / step) + 1);
      readout(k);
      if (now - t0 < total + 200) requestAnimationFrame(frame);
      else { building = false; stackBtn.removeAttribute("aria-disabled"); tower.removeAttribute("aria-busy"); readout(groups.length); }
    };
    requestAnimationFrame(frame);
  };
  if (reduce) stackBtn.hidden = true;
  stackBtn.addEventListener("click", () => {
    if (building) return;
    build();
    say(`${groups[groups.length - 1].n} pancakes, ${fmt(groups[groups.length - 1].h)} inches.`, 3200);
  });
  if (!reduce && "IntersectionObserver" in window) {
    groups.forEach(({ g }) => { g.style.opacity = 0; });
    mascot.style.opacity = 0;
    const io = new IntersectionObserver(entries => {
      if (!entries.some(e => e.isIntersecting)) return;
      io.disconnect();
      groups.forEach(({ g }) => { g.style.opacity = ""; });
      mascot.style.opacity = "";
      build();
    }, { threshold: .5 });
    io.observe(tower);
  }

  /* ---------- recipe: ratios and doses ---------- */
  const pctOf = Object.fromEntries(P.shopping.map(x => [x.key, x.pct]));
  $("#ratios").innerHTML = S.batter.ingredient.map(i => {
    const v = pctOf[i.key];
    return `<div class="ratio"><span class="name">${label(i.key)}</span><span class="track"><span class="bar" style="width:${Math.min(100, v / 150 * 100)}%"></span></span><span class="pct num">${Math.round(v)}</span><span class="why">${i.why}</span></div>`;
  }).join("");
  $("#doses").innerHTML = P.sizes.map(z =>
    `<div class="dose"><svg aria-hidden="true" style="--in:${z.ring_in}"><use href="#cake" width="100%" height="100%"/></svg><b>${z.ring_in} in · ${fmt(z.dose_cups, 2)} cup</b><small>${Math.round(z.dose_ml)} ml · ${z.per_batch} per batch · ${z.name}</small></div>`).join("");

  /* scrollable tables get a keyboard stop and a name (Safari doesn't focus scrollers) */
  const markScrollers = () => $$(".table-wrap").forEach(w => {
    const scrolls = w.scrollWidth > w.clientWidth + 1;
    if (scrolls) {
      w.tabIndex = 0;
      w.setAttribute("role", "region");
      w.setAttribute("aria-label", `${w.dataset.name || "Table"}, scrollable`);
    } else { w.removeAttribute("tabindex"); w.removeAttribute("role"); w.removeAttribute("aria-label"); }
  });

  /* ---------- calculator (port of calc.py) ---------- */
  const thick = $("#thick"), thickN = $("#thick-n"), settle = $("#settle"), spare = $("#spare");
  const radios = name => $$(`input[name="${name}"]`);
  const state = { thick: P.thickness_in, settle: T.settle_ratio, spare: S.cook.spare_ratio, attempts: 1, units: "us" };
  const defaults = { ...state };
  // the browser clamps and snaps a value set on a range input; read it back
  const snap = (input, v) => { input.value = String(v); return Number(input.value); };
  const q = new URLSearchParams(location.search);
  const num = k => { const raw = q.get(k); if (raw == null || !raw.trim()) return null; const v = Number(raw); return Number.isFinite(v) ? v : null; };
  // the spec values stay exact; only a value from the URL goes through the input's clamp and step
  thick.value = String(state.thick);
  settle.value = String(Math.round(state.settle * 100));
  spare.value = String(Math.round(state.spare * 100));
  if (num("t") != null) state.thick = snap(thick, num("t"));
  if (num("s") != null) state.settle = snap(settle, num("s")) / 100;
  if (num("x") != null) state.spare = snap(spare, num("x")) / 100;
  if (["1", "2", "3"].includes(q.get("a"))) state.attempts = Number(q.get("a"));
  if (["us", "metric"].includes(q.get("u"))) state.units = q.get("u");
  radios("attempts").forEach(r => { r.checked = Number(r.value) === state.attempts; });
  radios("units").forEach(r => { r.checked = r.value === state.units; });

  const compute = () => {
    const settled = state.thick * (1 - state.settle);
    let ml = 0, cook = 0, tower = 0, batches = 0;
    const sizes = S.size.map(z => {
      const dose = P.batch_ml / z.per_batch;
      const b = Math.ceil(Math.ceil(z.in_tower * state.attempts * (1 + state.spare)) / z.per_batch);
      const n = b * z.per_batch;
      ml += dose * n; cook += n; tower += z.in_tower; batches += b;
      return { ...z, n, dose, b };
    });
    return { sizes, ml, cook, tower, batches, height: tower * settled, toStop: Math.ceil(T.build_to_in / settled) };
  };
  const lbOz = g => {
    const oz = g / 28.3495;
    if (oz < 16) return `${fmt(oz)} oz`;
    const t = Math.round(oz), lb = Math.floor(t / 16), r = t % 16;
    return r ? `${lb} lb ${r} oz` : `${lb} lb`;
  };
  const shopping = r => {
    const us = state.units === "us", margin = (S.shopping && S.shopping.margin) || 0;
    return P.shopping.map(x => {
      let qty;
      if (x.unit === "can") qty = `${x.total * state.attempts} cans`;
      else {
        const tot = x.per_batch * r.batches, gr = x.g / P.batches * r.batches;
        if (x.unit === "egg") qty = `${tot} (${Math.ceil(tot * (1 + margin) / 12)} dozen)`;
        else if (x.unit === "cup") qty = us ? `${fmt(tot / 16, 2)} gal` : `${fmt(tot * .236588)} L`;
        else if (x.unit === "tsp") qty = us ? `${tot} tsp` : `${Math.round(gr)} g`;
        else qty = us ? lbOz(gr) : (gr >= 1000 ? `${fmt(gr / 1000, 1)} kg` : `${Math.round(gr)} g`);
      }
      return [label(x.key), qty];
    });
  };
  const OK = '<svg aria-hidden="true"><use href="#check"/></svg>';
  const render = (announce = false) => {
    const r = compute(), us = state.units === "us";
    const pct = (input) => `${(input.value - input.min) / (input.max - input.min) * 100}%`;
    thick.style.setProperty("--p", pct(thick));
    settle.style.setProperty("--p", pct(settle));
    spare.style.setProperty("--p", pct(spare));
    if (document.activeElement !== thickN) thickN.value = state.thick.toFixed(3);
    thick.setAttribute("aria-valuetext", `${state.thick.toFixed(3)} inches`);
    $("#settle-o").textContent = `${Math.round(state.settle * 100)}%`;
    settle.setAttribute("aria-valuetext", `${Math.round(state.settle * 100)} percent`);
    $("#spare-o").textContent = `${Math.round(state.spare * 100)}%`;
    spare.setAttribute("aria-valuetext", `${Math.round(state.spare * 100)} percent`);
    const max = 50;
    $("#g-fill").style.width = `${Math.min(100, r.height / max * 100)}%`;
    $("#g-rec").style.left = `${T.record_height_in / max * 100}%`;
    $("#g-stop").style.left = `${T.build_to_in / max * 100}%`;
    const ok = r.height >= T.build_to_in;
    const verdict = ok ? `${r.tower} pancakes reach ${fmt(r.height)} in. You stop at ${T.build_to_in}.`
                       : `${r.tower} pancakes only reach ${fmt(r.height)} in. You need ${r.toStop}.`;
    const v = $("#verdict");
    v.className = `verdict ${ok ? "ok" : "bad"}`;
    v.innerHTML = `${ok ? OK : ""}<span>${verdict}</span>`;
    $("#t-cook").textContent = r.cook;
    $("#t-batter").textContent = us ? `${fmt(r.ml / 3785.41)} gal` : `${fmt(r.ml / 1000)} L`;
    $("#t-stop").textContent = r.toStop;
    $("#t-sizes").innerHTML = `<caption class="sr-only">Pancakes per ring size</caption><thead><tr><th scope="col">Ring</th><th scope="col" class="r">In tower</th><th scope="col" class="r">To cook</th><th scope="col" class="r">Dose</th></tr></thead><tbody>` +
      r.sizes.map(z => `<tr><td>${cakeSwatch(z.name)}${z.ring_in} in ${z.name}</td><td class="r">${z.in_tower * state.attempts}</td><td class="r">${z.n}</td><td class="r">${us ? fmt(z.dose / 236.588, 2) + " cup" : Math.round(z.dose) + " ml"}</td></tr>`).join("") + "</tbody>";
    $("#t-shop").innerHTML = `<thead><tr><th scope="col">Shopping list</th><th scope="col" class="r">Amount</th></tr></thead><tbody>` +
      shopping(r).map(([k, qty]) => `<tr><td>${k}</td><td class="r">${qty}</td></tr>`).join("") + "</tbody>";
    const warns = [];
    if (state.thick > S.cook.reject_above_in || state.thick < S.cook.reject_below_in) warns.push(`Outside the accepted thickness band (${S.cook.reject_below_in}–${S.cook.reject_above_in} in). Fix the dose before you cook ${r.cook} of them.`);
    $("#warns").innerHTML = warns.map(w => `<p class="warn">${w}</p>`).join("");
    markScrollers();
    if (announce) say(verdict + (warns.length ? " " + warns[0] : ""), 600);
    return r;
  };

  const planUrl = () => {
    const p = new URLSearchParams();
    if (state.thick !== defaults.thick) p.set("t", state.thick.toFixed(3));
    if (state.settle !== defaults.settle) p.set("s", Math.round(state.settle * 100));
    if (state.spare !== defaults.spare) p.set("x", Math.round(state.spare * 100));
    if (state.attempts !== 1) p.set("a", state.attempts);
    if (state.units !== "us") p.set("u", state.units);
    const s = p.toString();
    return location.pathname + (s ? `?${s}` : "") + "#calculator";
  };
  let urlTimer;
  const saveUrl = () => {
    clearTimeout(urlTimer);
    urlTimer = setTimeout(() => { try { history.replaceState(null, "", planUrl()); } catch (e) { /* file:// or throttled */ } }, 300);
  };

  thick.addEventListener("input", () => { state.thick = Number(thick.value); render(true); });
  settle.addEventListener("input", () => { state.settle = Number(settle.value) / 100; render(true); });
  spare.addEventListener("input", () => { state.spare = Number(spare.value) / 100; render(true); });
  thickN.addEventListener("input", () => {
    const v = Number(thickN.value);
    if (!thickN.value || !Number.isFinite(v) || v < Number(thick.min) || v > Number(thick.max)) return;
    state.thick = snap(thick, v);
    render(true);
  });
  thickN.addEventListener("change", () => {
    const v = Number(thickN.value);
    state.thick = snap(thick, Number.isFinite(v) && thickN.value ? v : state.thick);
    thickN.value = state.thick.toFixed(3);
    render(true);
    saveUrl();
  });
  [thick, settle, spare].forEach(i => i.addEventListener("change", saveUrl));
  radios("attempts").forEach(r => r.addEventListener("change", () => { state.attempts = Number(r.value); render(true); saveUrl(); }));
  radios("units").forEach(r => r.addEventListener("change", () => { state.units = r.value; render(true); saveUrl(); }));
  $("#calc-form").addEventListener("submit", e => e.preventDefault());
  render();

  const copyText = (text, done) => {
    const fallback = () => {
      const prev = document.activeElement;
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.readOnly = true;
      ta.style.cssText = "position:fixed;top:0;left:0;width:1px;height:1px;opacity:0;font-size:16px";
      document.body.append(ta);
      ta.focus({ preventScroll: true });
      ta.select();
      ta.setSelectionRange(0, text.length);
      let ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
      ta.remove();
      if (prev && prev.focus) prev.focus({ preventScroll: true });
      if (ok) toast(done); else window.prompt("Copy this:", text);
    };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(() => toast(done), fallback);
    else fallback();
  };
  $("#copy-shop").addEventListener("click", () => {
    const r = compute();
    const lines = shopping(r).map(([k, qty]) => `- ${k}: ${qty}`);
    copyText(`Pancake Tower shopping list (${state.attempts} attempt${state.attempts > 1 ? "s" : ""}, ${r.batches} batches, ${state.thick.toFixed(3)} in)\n${lines.join("\n")}\n${location.origin}${planUrl()}`, "Shopping list copied");
  });
  $("#share-plan").addEventListener("click", () => {
    try { history.replaceState(null, "", planUrl()); } catch (e) { /* ignore */ }
    const url = location.origin + planUrl();
    if (navigator.share && matchMedia("(pointer: coarse)").matches) {
      navigator.share({ title: "Our Pancake Tower plan", url }).catch(e => { if (!e || e.name !== "AbortError") copyText(url, "Link to this plan copied"); });
    } else copyText(url, "Link to this plan copied");
  });

  /* ---------- record history: an SVG for wide cards, a list for narrow ones ---------- */
  const recs = D.records, rs = $("#rec-svg"), tip = $("#tip"), chart = $("#chart");
  const X0 = 52, X1 = 990, YB = 352, YT = 32, sc = (YB - YT) / 48;
  for (let v = 0; v <= 48; v += 12) {
    el("line", { x1: X0, x2: X1, y1: YB - v * sc, y2: YB - v * sc, stroke: v ? "#EFE4DC" : "#2C002A", "stroke-width": v ? 1 : 1.5 }, rs);
    el("text", { x: X0 - 12, y: YB - v * sc + 4, "text-anchor": "end", "font-family": "Geist, sans-serif", "font-size": 13, fill: "#6C4B65" }, rs).textContent = v;
  }
  const all = [...recs.map(r => ({ ...r, h: r.cm / 2.54 })), { year: Number(E.start.slice(0, 4)), place: E.place, holder: "Pancake", h: T.build_to_in, ours: true }];
  const band = (X1 - X0) / all.length, bw = Math.min(64, band * .56);
  const best = Math.max(...recs.map(r => r.cm));
  const tipText = r => r.ours ? `<b>${E.date} · ${T.build_to_in} in?</b><br>Pancake, ${E.place}. Our stop line.`
    : `<b>${r.year} · ${fmt(r.h)} in</b> (${r.cm} cm)<br>${r.holder}, ${r.place}${r.pancakes ? `<br>${r.pancakes} pancakes` : ""}`;
  all.forEach((r, i) => {
    const x = X0 + band * (i + .5), hh = r.h * sc;
    const gB = el("g", { class: "bar-g" }, rs);
    if (r.ours) el("rect", { x: x - bw / 2, y: YB - hh, width: bw, height: hh, rx: 10, fill: "#EFDDF1", stroke: "#8D43FD", "stroke-width": 2, "stroke-dasharray": "7 5" }, gB);
    else el("rect", { class: "fill", x: x - bw / 2, y: YB - hh, width: bw, height: hh, rx: 10, fill: "#FF7AA0" }, gB);
    el("text", { x, y: r.ours ? YB - hh - 10 : YB - hh + 22, "text-anchor": "middle", "font-family": "Geist, sans-serif", "font-size": 14, "font-weight": r.cm === best || r.ours ? 700 : 600, fill: r.ours ? "#8D43FD" : "#2C002A" }, gB).textContent = r.ours ? `${r.h}?` : fmt(r.h);
    el("text", { x, y: YB + 24, "text-anchor": "middle", "font-family": "Geist, sans-serif", "font-size": 14, "font-weight": 700, fill: r.ours ? "#8D43FD" : "#2C002A" }, rs).textContent = r.ours ? day : r.year;
    el("text", { x, y: YB + 44, "text-anchor": "middle", "font-family": "Geist, sans-serif", "font-size": 12, fill: "#6C4B65" }, rs).textContent = r.place;
    gB.addEventListener("pointerenter", e => {
      if (e.pointerType !== "mouse") return;
      tip.innerHTML = tipText(r);
      tip.hidden = false;
      const box = chart.getBoundingClientRect(), b = gB.getBoundingClientRect();
      tip.style.left = `${Math.min(box.width - 248, Math.max(8, b.left - box.left + b.width / 2 - 110))}px`;
      tip.style.top = `${b.top - box.top - tip.offsetHeight - 10}px`;
    });
    gB.addEventListener("pointerleave", () => { tip.hidden = true; });
  });
  document.addEventListener("keydown", e => { if (e.key === "Escape") tip.hidden = true; });
  const ry = YB - T.record_height_in * sc;
  el("line", { x1: X0, x2: X1, y1: ry, y2: ry, stroke: "#E33A6A", "stroke-width": 2, "stroke-dasharray": "6 5" }, rs);
  el("text", { x: X0 + 8, y: ry - 9, "font-family": "Geist, sans-serif", "font-size": 13, "font-weight": 600, fill: "#2C002A" }, rs).textContent = `Record to beat · ${T.record_height_in} in`;
  $("#rec-list").innerHTML = all.map(r =>
    `<li${r.ours ? ' class="ours"' : ""} style="--w:${(r.h / 50 * 100).toFixed(1)}"><span class="yr">${r.ours ? day : r.year}</span><span class="bar">${r.ours ? `${r.h}?` : fmt(r.h)} in</span><span class="place">${r.place}${r.pancakes ? ` · ${r.pancakes} pancakes` : ""}${r.ours ? " · our stop line" : ""}</span></li>`).join("");
  $("#rec-table").innerHTML = `<thead><tr><th scope="col">Year</th><th scope="col">Where</th><th scope="col">Who</th><th scope="col" class="r">Height</th><th scope="col" class="r">Pancakes</th></tr></thead><tbody>` +
    recs.map(r => `<tr><td class="num">${r.year}</td><td>${r.place}</td><td><a href="${r.source}">${r.holder}</a></td><td class="r">${fmt(r.cm / 2.54)} in</td><td class="r">${r.pancakes ?? "–"}</td></tr>`).join("") + "</tbody>";

  markScrollers();
  if ("ResizeObserver" in window) { const ro = new ResizeObserver(() => markScrollers()); $$(".table-wrap").forEach(w => ro.observe(w)); }
  $$("details").forEach(d => d.addEventListener("toggle", markScrollers));
  if (document.fonts) document.fonts.ready.then(markScrollers);

  /* ---------- reveal once: visible by default, animated only when it scrolls in ---------- */
  const reveal = (items, animate) => items.forEach((it, i) => {
    it.classList.remove("pending");
    if (animate) { it.style.setProperty("--d", `${i * 64}ms`); it.classList.add("in"); }
  });
  if (!reduce && "IntersectionObserver" in window) {
    const pending = new Set();
    const io = new IntersectionObserver(entries => {
      const now = entries.filter(e => e.isIntersecting && pending.has(e.target)).map(e => e.target);
      now.forEach(t => { pending.delete(t); io.unobserve(t); });
      reveal(now, true);
    }, { rootMargin: "0px 0px -12% 0px" });
    $$("[data-reveal]").forEach(it => {
      if (it.getBoundingClientRect().top > innerHeight * .92) { it.classList.add("pending"); pending.add(it); io.observe(it); }
    });
    // anything already above the viewport (restored scroll, anchor jumps) shows at once
    const sweep = () => {
      const passed = [...pending].filter(it => it.getBoundingClientRect().bottom < 0);
      passed.forEach(t => { pending.delete(t); io.unobserve(t); });
      reveal(passed, false);
      if (!pending.size) removeEventListener("scroll", onSweep);
    };
    let swept = false;
    const onSweep = () => { if (!swept) { swept = true; requestAnimationFrame(() => { swept = false; sweep(); }); } };
    addEventListener("scroll", onSweep, { passive: true });
    addEventListener("load", sweep);
  }
  addEventListener("beforeprint", () => {
    reveal($$("[data-reveal].pending"), false);
    $$("details").forEach(d => { d.open = true; });
    groups.forEach(({ g }) => { g.style.opacity = ""; });
    mascot.style.opacity = "";
  });
})();
