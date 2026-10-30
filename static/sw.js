const V = 'awb-__V__';
const STATIC = ['/static/icon-192.png', '/static/apple-touch-icon.png', '/static/manifest.webmanifest'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(V + '-static').then((c) => c.addAll(STATIC)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => !k.startsWith(V)).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('push', (e) => {
  const d = e.data ? e.data.json() : {};
  e.waitUntil(self.registration.showNotification(d.title || 'AgentWorkbench', { body: d.body || '', data: { url: d.url || '/' }, icon: '/static/icon-192.png' }));
});

self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const url = new URL((e.notification.data && e.notification.data.url) || '/', self.location.origin).href;
  e.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then((all) => {
    const win = all.find((c) => 'focus' in c);
    if (!win) return clients.openWindow(url);
    return win.focus().then((c) => (c || win).navigate(url)).catch(() => clients.openWindow(url));
  }));
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  if (url.pathname.startsWith('/static/')) {
    e.respondWith(caches.open(V + '-static').then((cache) => cache.match(req).then((hit) => {
      const net = fetch(req).then((res) => { if (res.ok) cache.put(req, res.clone()); return res; }).catch(() => hit);
      return hit || net;
    })));
    return;
  }
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).then((res) => {
      if (res.ok && !res.redirected) { const copy = res.clone(); caches.open(V + '-pages').then((c) => c.put(req, copy)); }
      return res;
    }).catch(() => caches.open(V + '-pages').then((c) => c.match(req).then((hit) => hit || c.match('/')))
      .then((hit) => hit || new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } }))));
  }
});
