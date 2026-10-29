(function () {
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(function () {});

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
