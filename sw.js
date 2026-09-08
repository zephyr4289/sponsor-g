/*
 * KnowYourSponsor service worker — deliberately minimal.
 *
 * Strategy:
 *   HTML pages   network-first, and with cache:'no-cache' so the browser
 *                must revalidate. A push goes live on the very next load
 *                rather than the one after it.
 *   data/*.json  network-first for the same reason — a stale register is
 *                worse than a slow one.
 *   other assets stale-while-revalidate. Icons and images are content-stable
 *                and worth serving instantly from cache.
 *
 * The cache is therefore an offline fallback, not a speed-up for pages.
 * That is a deliberate trade: correctness over ~200ms on repeat loads.
 *
 * Bump CACHE when the shell changes to evict the old one.
 */
const CACHE = 'knowyoursponsor-v1';

const SHELL = [
  './',
  './index.html',
  './manifest.json',
  './favicon.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
];

self.addEventListener('install', event => {
  event.waitUntil(
    // addAll rejects the whole install if any single entry 404s, so add
    // them individually and tolerate misses.
    caches.open(CACHE)
      .then(cache => Promise.all(
        SHELL.map(url => cache.add(url).catch(() => {}))
      ))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;

  // Never touch anything but same-origin GETs (analytics, fonts, form posts).
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  const isPage = request.mode === 'navigate' ||
                 request.destination === 'document';

  if (isPage || url.pathname.includes('/data/')) {
    event.respondWith(networkFirst(request));
  } else {
    event.respondWith(staleWhileRevalidate(request));
  }
});

async function networkFirst(request) {
  try {
    // cache:'no-cache' revalidates with the server instead of trusting the
    // HTTP cache. GitHub Pages serves max-age=600, which would otherwise
    // pin a just-replaced page for up to ten minutes.
    const response = await fetch(request.url, {
      cache: 'no-cache',
      credentials: 'same-origin',
    });
    if (response && response.ok) {
      const cache = await caches.open(CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    // Offline: fall back to whatever was cached, keyed by the original
    // request so a navigation still resolves to the cached shell.
    const cached = await caches.match(request) ||
                   await caches.match(request.url);
    if (cached) return cached;
    throw err;
  }
}

async function staleWhileRevalidate(request) {
  const cached = await caches.match(request);
  const network = fetch(request)
    .then(response => {
      if (response && response.ok) {
        caches.open(CACHE).then(cache => cache.put(request, response.clone()));
      }
      return response;
    })
    .catch(() => null);

  return cached || network.then(r => r || Response.error());
}
