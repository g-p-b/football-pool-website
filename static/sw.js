const CACHE = 'football-pool-v1';

const PRECACHE = [
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/dashboard.js',
  '/static/js/admin.js',
];

// Install: pre-cache static assets
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(PRECACHE))
  );
  self.skipWaiting();
});

// Activate: remove old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch strategy:
//   Static assets  → cache-first (fast loads)
//   Everything else → network-first (always fresh data)
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;

  const url = new URL(e.request.url);

  if (url.pathname.startsWith('/static/')) {
    // Cache-first for CSS/JS/fonts/icons
    e.respondWith(
      caches.match(e.request).then(cached => {
        if (cached) return cached;
        return fetch(e.request).then(resp => {
          const copy = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy));
          return resp;
        });
      })
    );
    return;
  }

  // Network-first for pages and API calls
  e.respondWith(
    fetch(e.request).catch(() =>
      new Response(
        '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Offline</title>' +
        '<meta name="viewport" content="width=device-width,initial-scale=1">' +
        '<style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;' +
        'height:100vh;margin:0;background:#16162a;color:#eee;text-align:center}' +
        'h2{font-size:2rem}p{color:#aaa}</style></head>' +
        '<body><div><div style="font-size:3rem">⚽</div>' +
        '<h2>You\'re offline</h2>' +
        '<p>Check your connection and try again.</p>' +
        '<button onclick="location.reload()" style="margin-top:1rem;padding:10px 24px;' +
        'background:#00c853;border:none;border-radius:8px;color:#fff;font-size:1rem;cursor:pointer">' +
        'Retry</button></div></body></html>',
        { headers: { 'Content-Type': 'text/html' } }
      )
    )
  );
});
