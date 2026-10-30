(function () {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').then(function (reg) {
      document.addEventListener('visibilitychange', function () { if (!document.hidden) reg.update(); });
    }).catch(function () {});
    var reloaded = false;
    navigator.serviceWorker.addEventListener('controllerchange', function () {
      if (!reloaded && navigator.serviceWorker.controller) { reloaded = true; location.reload(); }
    });
  }

  var mobile = window.matchMedia('(max-width:700px)').matches;

  // Collapsible sections on the project page (open on desktop, closed on the phone)
  document.querySelectorAll('details[data-closed-mobile]').forEach(function (d) { d.open = !mobile; });

  // Today / Projects tabs on the start page (the bottom bar switches the view without reloading)
  var tabLinks = document.querySelectorAll('.tabbar [data-tab-link]');
  if (document.querySelector('[data-tab]') && tabLinks.length) {
    var setTab = function (name) {
      document.body.dataset.tab = name;
      try { sessionStorage.setItem('awb-tab', name); } catch (e) {}
      tabLinks.forEach(function (a) {
        if (a.dataset.tabLink === name) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
      });
    };
    var wanted = new URLSearchParams(location.search).get('tab') || (function () { try { return sessionStorage.getItem('awb-tab'); } catch (e) { return null; } })() || 'today';
    setTab(wanted === 'projects' ? 'projects' : 'today');
    tabLinks.forEach(function (a) {
      a.addEventListener('click', function (e) { e.preventDefault(); setTab(a.dataset.tabLink); window.scrollTo(0, 0); });
    });
  }

  // Project page: one section at a time (tasks, notes, documents, activity)
  var ptabLinks = document.querySelectorAll('[data-ptab-link]');
  if (ptabLinks.length) {
    var setPtab = function (name, keepHash) {
      document.body.dataset.ptab = name;
      ptabLinks.forEach(function (b) { b.classList.toggle('on', b.dataset.ptabLink === name); });
      if (!keepHash) history.replaceState(null, '', name === 'tasks' ? location.pathname + location.search : '#' + name);
    };
    var hash = location.hash.replace('#', '');
    var start = hash.indexOf('doc') === 0 ? 'docs' : (['notes', 'docs', 'log'].indexOf(hash) >= 0 ? hash : 'tasks');
    setPtab(start, true);
    ptabLinks.forEach(function (b) { b.addEventListener('click', function () { setPtab(b.dataset.ptabLink); }); });
    if (hash.indexOf('doc-') === 0) { var target = document.getElementById(hash); if (target) { target.open = true; target.scrollIntoView(); } }
  }

  // Inbox: only the first two entries on the phone
  var inbox = document.querySelector('.inbox[data-more]');
  if (inbox && mobile) {
    inbox.querySelectorAll('.sheet').forEach(function (sheet) {
      var tasks = sheet.querySelectorAll('.task');
      if (tasks.length <= 2) return;
      tasks.forEach(function (t, i) { if (i >= 2) t.hidden = true; });
      var more = document.createElement('button');
      more.type = 'button'; more.className = 'linklike';
      more.textContent = inbox.dataset.more.replace('{n}', tasks.length);
      more.addEventListener('click', function () { tasks.forEach(function (t) { t.hidden = false; }); more.remove(); });
      sheet.appendChild(more);
    });
  }

  // Pull to refresh (iOS home-screen apps have none of their own)
  if (navigator.standalone || window.matchMedia('(display-mode: standalone)').matches) {
    var ind = document.createElement('div');
    ind.className = 'ptr';
    ind.textContent = '↻';
    document.body.appendChild(ind);
    var py = null, pull = 0;
    document.addEventListener('touchstart', function (e) {
      py = window.scrollY <= 0 && e.touches.length === 1 && !e.target.closest('dialog,textarea,input,select') ? e.touches[0].clientY : null;
      pull = 0;
    }, { passive: true });
    document.addEventListener('touchmove', function (e) {
      if (py === null) return;
      pull = e.touches[0].clientY - py;
      if (pull > 0) {
        ind.style.opacity = Math.min(pull / 80, 1);
        ind.style.transform = 'translate(-50%,' + Math.min(pull, 120) / 2 + 'px) rotate(' + pull * 3 + 'deg)';
      } else { py = null; ind.style.opacity = 0; }
    }, { passive: true });
    document.addEventListener('touchend', function () {
      if (py !== null && pull > 90) { ind.classList.add('spin'); location.reload(); }
      else { ind.style.opacity = 0; ind.style.transform = 'translate(-50%,0)'; }
      py = null;
    });
  }

  var touchOS = /iPhone|iPad|iPod|Android/.test(navigator.userAgent) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  if (!touchOS && window.matchMedia('(hover:hover) and (pointer:fine)').matches) document.documentElement.classList.add('desk');

  document.addEventListener('submit', function (e) {
    if (e.target.getAttribute('action') === '/logout' && window.caches) {
      caches.keys().then(function (ks) { ks.filter(function (k) { return k.indexOf('-pages') > 0; }).forEach(function (k) { caches.delete(k); }); });
    }
  });

  // Swipe a task card to the left to mark it done
  document.querySelectorAll('.card[data-id]').forEach(function (card) {
    var x0 = null, y0 = 0, dx = 0;
    card.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; dx = 0; }, { passive: true });
    card.addEventListener('touchmove', function (e) {
      if (x0 === null) return;
      dx = e.touches[0].clientX - x0;
      if (Math.abs(e.touches[0].clientY - y0) > Math.abs(dx)) { x0 = null; card.style.transform = ''; return; }
      if (dx < 0) card.style.transform = 'translateX(' + dx + 'px)';
    }, { passive: true });
    card.addEventListener('touchend', function () {
      if (x0 !== null && dx < -90) {
        card.style.opacity = '.3';
        fetch('/t/' + card.dataset.id + '/toggle', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: 'next=/' })
          .then(function (r) { if (r.ok) { if (window.keepScroll) window.keepScroll(); location.reload(); } else { card.style.opacity = ''; card.style.transform = ''; } })
          .catch(function () { card.style.opacity = ''; card.style.transform = ''; });
      } else { card.style.transform = ''; }
      x0 = null;
    });
  });

  // Push notifications (iOS: only for the installed home-screen app)
  var pb = document.getElementById('push-btn');
  if (pb && 'serviceWorker' in navigator && 'PushManager' in window && Notification.permission !== 'granted') {
    pb.hidden = false;
    pb.addEventListener('click', function () {
      Notification.requestPermission().then(function (perm) {
        if (perm !== 'granted') return;
        return navigator.serviceWorker.ready.then(function (reg) {
          return fetch('/push/key').then(function (r) { return r.json(); }).then(function (k) {
            var pad = '='.repeat((4 - k.key.length % 4) % 4), b64 = (k.key + pad).replace(/-/g, '+').replace(/_/g, '/');
            var key = Uint8Array.from(atob(b64), function (c) { return c.charCodeAt(0); });
            return reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: key });
          });
        }).then(function (sub) {
          return fetch('/push/subscribe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(sub) });
        }).then(function () { pb.hidden = true; return fetch('/push/test', { method: 'POST' }); });
      });
    });
  }

  // Quick add (works offline: queued entries are sent as soon as the connection is back)
  var dlg = document.getElementById('qa');
  if (!dlg) return;
  var QKEY = 'awb-queue';
  function queue() { try { return JSON.parse(localStorage.getItem(QKEY) || '[]'); } catch (e) { return []; } }
  function save(q) { try { localStorage.setItem(QKEY, JSON.stringify(q)); } catch (e) {} }
  function post(item) {
    return fetch('/p/' + encodeURIComponent(item.project) + '/add', {
      method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ text: item.text, prio: item.prio, kind: item.kind })
    }).then(function (r) { if (!r.ok) throw new Error(r.status); });
  }
  function flush() {
    var q = queue();
    if (!q.length || !navigator.onLine) return;
    post(q[0]).then(function () { save(queue().slice(1)); flush(); }).catch(function () {});
  }
  window.addEventListener('online', flush);
  flush();
  document.getElementById('qa-open').addEventListener('click', function () {
    dlg.showModal();
    document.getElementById('qa-text').focus();
  });
  document.getElementById('qa-cancel').addEventListener('click', function () { dlg.close(); });
  document.getElementById('qa-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var text = document.getElementById('qa-text').value.trim();
    if (!text) return;
    var item = {
      project: document.getElementById('qa-project').value, text: text,
      prio: (document.querySelector('input[name=qa-prio]:checked') || {}).value || '2',
      kind: document.getElementById('qa-kind').value
    };
    document.getElementById('qa-text').value = '';
    dlg.close();
    post(item).then(function () { location.reload(); }).catch(function () {
      var q = queue(); q.push(item); save(q);
      var n = document.getElementById('qa-note');
      n.textContent = n.dataset.queued; n.hidden = false;
    });
  });
})();
