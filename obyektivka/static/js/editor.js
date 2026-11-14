/*
 * Obyektivka editor (Alpine.js komponenti).
 *
 * Holat (S) faqat brauzerda: localStorage. Har o'zgarishda body'da "obv-changed" hodisasi
 * chiqariladi -> HTMX (#pvTrigger, delay:300ms) holatni JSON qilib /api/preview ga yuboradi
 * va o'ng paneldagi varaqni almashtiradi. Mantiq prototipdagi (reference/obyektivka.html) bilan bir xil.
 */
(function () {
  'use strict';

  const STORE = 'obyektivka-draft-v2';
  const KEYS = ['fish', 'lavozim', 'tugSana', 'tugJoy', 'millati', 'partiya', 'malumoti', 'tamomlagan',
    'mutaxassislik', 'ilmiyDaraja', 'ilmiyUnvon', 'tillar', 'mukofot', 'deputat'];
  const MEHNAT_F = ['dan', 'gacha', 'matn'];
  const REL_F = ['rel', 'fish', 'yil', 'joy', 'ish', 'turar'];
  const LANGS = ['new', 'lat', 'cyr', 'ru'];
  const MAX_PHOTO = 5 * 1024 * 1024;

  // editor.js (defer) DOMContentLoaded'dan oldin bajariladi — HTMX tayyorligini shu bayroq bilan bilamiz
  let domReady = document.readyState === 'complete';
  document.addEventListener('DOMContentLoaded', () => { setTimeout(() => { domReady = true; }, 0); });

  const has = s => !!(s && String(s).trim());
  const clone = o => JSON.parse(JSON.stringify(o));
  let uid = 0;
  const newId = () => 'r' + Date.now().toString(36) + (uid++).toString(36);

  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* to'lgan yoki taqiqlangan */ } }

  function csrf() {
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  /* Har qanday kiruvchi obyektni (localStorage, JSON import, prototip formati) to'g'ri shaklga keltiradi */
  function normalize(o, lang) {
    o = (o && typeof o === 'object' && !Array.isArray(o)) ? o : {};
    const str = v => (v == null ? '' : String(v));
    const out = { lang: LANGS.includes(o.lang) ? o.lang : lang, photo: '' };
    KEYS.forEach(k => { out[k] = str(o[k]); });
    out.photo = typeof o.photo === 'string' && /^data:image\/(jpeg|png);base64,/.test(o.photo) ? o.photo : '';
    const rows = (arr, fields) => (Array.isArray(arr) ? arr : []).filter(x => x && typeof x === 'object')
      .slice(0, 60).map(x => { const r = { _id: newId() }; fields.forEach(f => { r[f] = str(x[f]); }); return r; });
    out.mehnat = rows(o.mehnat, MEHNAT_F);
    out.qarindosh = rows(o.qarindosh, REL_F);
    return out;
  }

  /* Serverga / faylga yuboriladigan toza ma'lumot (_id siz) */
  function plain(S) {
    const o = clone(S);
    o.mehnat.forEach(m => delete m._id);
    o.qarindosh.forEach(r => delete r._id);
    return o;
  }

  async function postJSON(url, body) {
    const res = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
      body: JSON.stringify(body),
    });
    return res;
  }

  document.addEventListener('alpine:init', () => {
    window.Alpine.data('editor', () => {
      const boot = JSON.parse(document.getElementById('obv-boot').textContent);
      const U = boot.ui;
      const lang = boot.lang;

      // Cropper va fayl reaktiv bo'lmasin (Alpine proxy'si Cropper ichki holatini buzadi)
      let cropper = null;
      let cropFile = null;

      const blank = () => normalize({
        lang,
        mehnat: [{ dan: '', gacha: '', matn: '' }],
        qarindosh: [{ rel: U.rels[0] }, { rel: U.rels[1] }],
      }, lang);

      return {
        U, lang, urls: boot.urls,
        S: blank(),
        errors: {},
        tab: 'form',
        busy: { pdf: false, docx: false, photo: false },
        toast: { show: false, msg: '', action: false, actionLabel: '' },
        _toastFn: null,
        modal: { show: false, text: '' },
        _modalResolve: null,
        crop: { show: false },
        lastField: null,
        _saveT: null, _toastT: null, _lastScroll: 0,

        /* ---------------- ishga tushirish ---------------- */
        init() {
          const raw = lsGet(STORE);
          let stored = null;
          try { stored = raw ? JSON.parse(raw) : null; } catch (e) { stored = null; }
          if (stored) this.S = normalize(stored, lang);

          this.$watch('S', () => { this.changed(); this.save(); });
          this.setupSortable();
          this.setupFit();
          document.body.addEventListener('htmx:configRequest', e => {
            if (e.detail.elt && e.detail.elt.id === 'pvTrigger') {
              e.detail.parameters.payload = JSON.stringify(plain(this.S));
            }
          });
          document.body.addEventListener('htmx:afterSwap', e => {
            if (e.detail.target && e.detail.target.id === 'preview') this.flashLast();
          });
          document.body.addEventListener('htmx:responseError', e => {
            if (e.detail.xhr && e.detail.xhr.status === 429) this.showToast(U.tRate);
          });
          document.body.addEventListener('htmx:sendError', () => this.showToast(U.tNet));

          // Saqlangan ma'lumot boshqa tilda bo'lsa (masalan, tilni almashtirib keldi) — o'giramiz
          if (stored && LANGS.includes(stored.lang) && stored.lang !== lang) {
            this.convertFrom(stored.lang);
          } else {
            this.S.lang = lang;
            this.changed();
          }
        },

        /* ---------------- til / yozuv ---------------- */
        async convertFrom(from) {
          const prev = plain(this.S);
          prev.lang = from;
          try {
            const res = await postJSON(this.urls.convert, { data: prev, from, to: lang });
            if (!res.ok) throw new Error(String(res.status));
            const out = await res.json();
            this.S = normalize(out.data, lang);
            this.save(true);
            if (out.toast === 'tConv') {
              this.showToast(U.tConv, 5000, {
                label: U.undo,
                fn: () => { lsSet(STORE, JSON.stringify(prev)); location.href = this.urls.langs[from]; },
              });
            } else if (out.toast) {
              this.showToast(U[out.toast], 4000);
            }
          } catch (e) {
            this.S.lang = lang;
            this.showToast(U.tNet);
          }
          this.changed();
        },

        /* ---------------- holat ---------------- */
        save(now) {
          clearTimeout(this._saveT);
          const run = () => lsSet(STORE, JSON.stringify(plain(this.S)));
          if (now) run(); else this._saveT = setTimeout(run, 300);
        },
        changed() {
          // Alpine HTMX'dan oldin ishga tushishi mumkin: HTMX DOM'ni qayta ishlagach yuboramiz
          const fire = () => document.body.dispatchEvent(new CustomEvent('obv-changed'));
          if (domReady) fire();
          else document.addEventListener('DOMContentLoaded', () => setTimeout(fire, 0), { once: true });
        },
        get progress() {
          const S = this.S;
          let n = KEYS.filter(k => has(S[k])).length;
          const t = KEYS.length + 3;
          if (S.photo) n++;
          if (S.mehnat.some(m => has(m.matn))) n++;
          if (S.qarindosh.some(r => has(r.fish))) n++;
          return Math.round(n / t * 100);
        },
        anyData() {
          return KEYS.some(k => has(this.S[k])) || this.S.mehnat.some(m => has(m.matn)) || this.S.qarindosh.some(r => has(r.fish));
        },

        /* Qaysi maydon yozilganini eslab qolamiz -> preview'da belgilash */
        onInput(e) {
          const el = e.target;
          if (el.dataset.k) {
            this.lastField = { sel: `[data-p="${el.dataset.k}"]` };
            if (this.errors[el.dataset.k] && el.dataset.k !== 'tugSana') delete this.errors[el.dataset.k];
          } else if (el.dataset.m || el.dataset.r) {
            const card = el.closest('.row-card');
            const list = el.dataset.m ? 'mehnat' : 'qarindosh';
            if (card) this.touched(list, +card.dataset.i);
          }
        },
        touched(list, i) {
          this.lastField = { sel: `[data-row="${list}"][data-i="${i}"]` };
        },
        chip(key, text, append) {
          text = text.trim();
          if (append) {
            const cur = (this.S[key] || '').split(',').map(s => s.trim()).filter(Boolean);
            if (!cur.includes(text)) cur.push(text);
            this.S[key] = cur.join(', ');
          } else {
            this.S[key] = text;
          }
          this.lastField = { sel: `[data-p="${key}"]` };
        },

        /* ---------------- sana / yil ---------------- */
        maskDate(e) {
          const el = e.target;
          if (e.inputType && e.inputType.startsWith('delete')) return;
          const d = el.value.replace(/\D/g, '').slice(0, 8);
          let o = d;
          if (d.length > 4) o = d.slice(0, 2) + '.' + d.slice(2, 4) + '.' + d.slice(4);
          else if (d.length > 2) o = d.slice(0, 2) + '.' + d.slice(2);
          if (o !== el.value) { el.value = o; this.S.tugSana = o; }
          if (o.length === 10) this.checkDate(); else delete this.errors.tugSana;
        },
        validDate(v) {
          v = (v || '').trim();
          if (!v) return true;
          const m = v.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
          if (!m) return false;
          const d = +m[1], mo = +m[2], y = +m[3];
          const dt = new Date(y, mo - 1, d);
          return dt.getFullYear() === y && dt.getMonth() === mo - 1 && dt.getDate() === d &&
            y >= 1900 && y <= new Date().getFullYear();
        },
        checkDate() {
          if (this.validDate(this.S.tugSana)) delete this.errors.tugSana;
          else this.errors.tugSana = 'errDate';
        },
        checkYear(loc, v) {
          v = (v || '').trim();
          if (!v || (/^\d{4}$/.test(v) && +v >= 1900 && +v <= 2100)) delete this.errors[loc];
          else this.errors[loc] = 'errYear';
        },
        serverErrors(detail) {
          // Jonli preview xatolari: server endi xato demagan maydonlardan belgini olamiz.
          // Yangi xatolarni yozish paytida ko'rsatmaymiz (chala sana/yil) — ular blur'da yoki eksportda chiqadi.
          const locs = new Set(((detail && detail.errors) || []).map(e => e.loc));
          const keep = {};
          Object.keys(this.errors).forEach(k => { if (locs.has(k)) keep[k] = this.errors[k]; });
          this.errors = keep;
        },
        markErrors(list) {
          const next = {};
          (list || []).forEach(e => { next[e.loc] = e.key; });
          this.errors = next;
          const first = list && list[0];
          if (first) {
            this.setTab('form');
            const [k, i, f] = first.loc.split('.');
            let el = null;
            if (i === undefined) el = document.getElementById('f-' + k);
            else {
              const row = (k === 'mehnat' ? this.S.mehnat : this.S.qarindosh)[+i];
              if (row) el = document.getElementById((k === 'mehnat' ? 'm-' : 'r-') + f + '-' + row._id);
            }
            if (el) {
              const det = el.closest('details');
              if (det) det.open = true;
              setTimeout(() => el.focus(), 30);
            }
          }
        },

        /* ---------------- ro'yxatlar ---------------- */
        addMehnat() {
          const last = this.S.mehnat[this.S.mehnat.length - 1];
          this.S.mehnat.push({ _id: newId(), dan: (last && last.gacha) || '', gacha: '', matn: '' });
          this.$nextTick(() => {
            const ins = this.$refs.mehnatList.querySelectorAll('textarea');
            if (ins.length) ins[ins.length - 1].focus();
          });
        },
        addRel() {
          const last = this.S.qarindosh[this.S.qarindosh.length - 1];
          this.S.qarindosh.push({ _id: newId(), rel: '', fish: '', yil: '', joy: '', ish: '', turar: last ? last.turar : '' });
          this.$nextTick(() => {
            const ins = this.$refs.relList.querySelectorAll('[data-r="rel"]');
            if (ins.length) ins[ins.length - 1].focus();
          });
        },
        removeRow(list, i) {
          this.S[list].splice(i, 1);
          this.errors = {};
        },
        move(list, i, dir) {
          const arr = this.S[list], j = i + dir;
          if (j < 0 || j >= arr.length) return;
          const [x] = arr.splice(i, 1);
          arr.splice(j, 0, x);
          this.touched(list, j);
          this.errors = {};
        },
        setupSortable() {
          if (!window.Sortable) return;
          const make = (el, list) => window.Sortable.create(el, {
            handle: '.drag-handle', draggable: '.row-card', animation: 150,
            onEnd: evt => {
              const from = evt.oldDraggableIndex, to = evt.newDraggableIndex;
              if (from === to || from == null || to == null) return;
              // DOM'ni joyiga qaytaramiz — tartibni Alpine (x-for) massiv orqali chizadi
              const item = evt.item, parent = evt.from;
              parent.removeChild(item);
              const cards = parent.querySelectorAll(':scope > .row-card');
              parent.insertBefore(item, cards[from] || null);
              const arr = this.S[list];
              const [x] = arr.splice(from, 1);
              arr.splice(to, 0, x);
              this.touched(list, to);
            },
          });
          make(this.$refs.mehnatList, 'mehnat');
          make(this.$refs.relList, 'qarindosh');
        },

        /* ---------------- rasm ---------------- */
        pickPhoto(e) {
          const f = e.target.files && e.target.files[0];
          e.target.value = '';
          if (!f) return;
          if (f.size > MAX_PHOTO) { this.showToast(U.tTooBig); return; }
          if (!/^image\/(jpeg|png|webp)$/.test(f.type)) { this.showToast(U.tPhotoType); return; }
          if (!window.Cropper) { this.uploadPhoto(f, null); return; }
          cropFile = f;
          this.crop.show = true;
          const img = this.$refs.cropImg;
          if (img.src) URL.revokeObjectURL(img.src);
          img.src = URL.createObjectURL(f);
          this.$nextTick(() => {
            if (cropper) cropper.destroy();
            cropper = new window.Cropper(img, {
              aspectRatio: 3 / 4, viewMode: 1, autoCropArea: 1, background: false, checkOrientation: true,
            });
          });
        },
        rotateCrop() { if (cropper) cropper.rotate(90); },
        closeCropper() {
          if (cropper) { cropper.destroy(); cropper = null; }
          const img = this.$refs.cropImg;
          if (img.src) { URL.revokeObjectURL(img.src); img.removeAttribute('src'); }
          this.crop.show = false;
        },
        cancelCrop() { cropFile = null; this.closeCropper(); },
        async applyCrop() {
          const data = cropper ? cropper.getData(true) : null;
          await this.uploadPhoto(cropFile, data);
          cropFile = null;
          this.closeCropper();
        },
        async uploadPhoto(file, cropData) {
          this.busy.photo = true;
          try {
            const fd = new FormData();
            fd.append('photo', file);
            if (cropData) fd.append('crop', JSON.stringify(cropData));
            const res = await fetch(this.urls.photo, {
              method: 'POST', body: fd, credentials: 'same-origin', headers: { 'X-CSRFToken': csrf() },
            });
            const out = await res.json().catch(() => ({}));
            if (!res.ok) { this.showToast(U[out.key] || U.tPhotoErr); return; }
            this.S.photo = out.photo;
            this.lastField = { sel: '[data-p="photo"]' };
          } catch (e) {
            this.showToast(U.tNet);
          } finally {
            this.busy.photo = false;
          }
        },
        removePhoto() { this.S.photo = ''; this.lastField = { sel: '[data-p="photo"]' }; },

        /* ---------------- namuna / tozalash ---------------- */
        async sample() {
          if (KEYS.some(k => has(this.S[k])) && !(await this.confirm(U.mSampleX))) return;
          const photo = this.S.photo;
          this.S = normalize({ ...clone(boot.sample), lang, photo }, lang);
          this.errors = {};
          this.showToast(U.tSample);
        },
        async clearAll() {
          if (!(await this.confirm(U.mClearX))) return;
          this.S = blank();
          this.errors = {};
          this.showToast(U.tCleared);
        },

        /* ---------------- eksport ---------------- */
        fname(ext) {
          const n = (has(this.S.fish) ? this.S.fish : U.fname).replace(/[\\/:*?"<>|]+/g, '').trim().replace(/\s+/g, '_');
          return `${n}_obyektivka.${ext}`;
        },
        download(blob, name) {
          const a = document.createElement('a');
          a.href = URL.createObjectURL(blob);
          a.download = name;
          document.body.appendChild(a);
          a.click();
          setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 2000);
        },
        async exportFile(kind) {
          if (this.busy[kind]) return;
          this.busy[kind] = true;
          try {
            const res = await postJSON(this.urls[kind], { data: plain(this.S) });
            if (res.status === 422) {
              const out = await res.json();
              this.markErrors(out.errors);
              this.showToast(U.tInvalid);
              return;
            }
            if (res.status === 429) { this.showToast(U.tRate); return; }
            if (!res.ok) throw new Error(String(res.status));
            const blob = await res.blob();
            const hdr = res.headers.get('X-Filename');
            this.download(blob, hdr ? decodeURIComponent(hdr) : this.fname(kind));
            this.showToast(U.tDl);
          } catch (e) {
            this.showToast(kind === 'pdf' ? U.tPdfErr : U.tWordErr);
          } finally {
            this.busy[kind] = false;
          }
        },
        exportJson() {
          const data = { format: 'obyektivka', version: 1, ...plain(this.S) };
          const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
          this.download(blob, this.fname('json'));
        },
        importJson(e) {
          const f = e.target.files && e.target.files[0];
          e.target.value = '';
          if (!f) return;
          if (f.size > 8 * 1024 * 1024) { this.showToast(U.tImportErr); return; }
          const reader = new FileReader();
          reader.onload = () => {
            let obj;
            try { obj = JSON.parse(String(reader.result)); } catch (err) { this.showToast(U.tImportErr); return; }
            if (!obj || typeof obj !== 'object' || Array.isArray(obj)) { this.showToast(U.tImportErr); return; }
            const src = LANGS.includes(obj.lang) ? obj.lang : lang;
            this.S = normalize(obj, src);
            this.errors = {};
            if (src !== lang) this.convertFrom(src);
            else this.showToast(U.tImported);
          };
          reader.onerror = () => this.showToast(U.tImportErr);
          reader.readAsText(f);
        },

        /* ---------------- preview: belgilash va scroll ---------------- */
        flashLast() {
          const lf = this.lastField;
          this.lastField = null;
          if (!lf) return;
          const els = document.querySelectorAll('#preview ' + lf.sel);
          els.forEach(el => { el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash'); });
          if (els[0]) this.scrollToEl(els[0]);
        },
        scrollToEl(el) {
          const now = Date.now();
          if (now - this._lastScroll < 400) return;
          this._lastScroll = now;
          const pane = this.$refs.pane;
          const r = el.getBoundingClientRect(), pr = pane.getBoundingClientRect();
          if (r.top < pr.top + 40 || r.bottom > pr.bottom - 40) {
            const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            pane.scrollBy({ top: r.top - pr.top - pr.height / 3, behavior: reduce ? 'auto' : 'smooth' });
          }
        },
        setupFit() {
          const pane = this.$refs.pane, wrap = this.$refs.wrap;
          const fit = () => {
            const avail = pane.clientWidth - (window.innerWidth < 900 ? 20 : 48);
            wrap.style.zoom = Math.min(1, Math.max(0.2, avail / 794));
          };
          try { new ResizeObserver(fit).observe(pane); } catch (e) { window.addEventListener('resize', fit); }
          fit();
          this._fit = fit;
        },
        setTab(t) {
          this.tab = t;
          this.$nextTick(() => this._fit && this._fit());
        },

        /* ---------------- toast / modal ---------------- */
        showToast(msg, ms = 2600, action = null) {
          this.toast.msg = msg;
          // Diqqat: funksiyani shablon ko'radigan maydonga qo'ymaymiz — Alpine ifodadagi funksiyani chaqirib yuboradi
          this._toastFn = action ? action.fn : null;
          this.toast.action = !!action;
          this.toast.actionLabel = action ? action.label : '';
          this.toast.show = true;
          clearTimeout(this._toastT);
          this._toastT = setTimeout(() => { this.toast.show = false; }, ms);
        },
        toastAction() {
          const fn = this._toastFn;
          this._toastFn = null;
          this.toast.show = false;
          if (fn) fn();
        },
        confirm(text) {
          return new Promise(resolve => {
            this.modal.text = text;
            this._modalResolve = resolve;
            this.modal.show = true;
          });
        },
        closeModal(v) {
          const r = this._modalResolve;
          this.modal.show = false;
          this._modalResolve = null;
          if (r) r(v);
        },
        onEscape() {
          if (this.modal.show) this.closeModal(false);
          else if (this.crop.show) this.cancelCrop();
        },
      };
    });
  });
})();
