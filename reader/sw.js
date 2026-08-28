/* escolib service worker.
   No library precache: whatever a lecture loads (text, timeline) is
   cached AS IT GOES and only serves as the offline fallback — every
   request is network-first, so a reload always gets fresh content.
   iOS key point: the <audio> requests the mp3 with Range requests — a
   cached mp3 must be answered 206 by slicing the stored blob. Audio is
   not cached yet (streaming only); a per-lecture download will come. */
const V = 'escolib-v38';
const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon-180.png',
  './icon-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(V).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks
        .filter((k) => (k.startsWith('escolib-') || k.startsWith('audiolib-')) && k !== V)
        .map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function rangeResponse(req, cache) {
  const full = await cache.match(req.url, { ignoreSearch: true });
  if (!full) return fetch(req);
  const blob = await full.blob();
  const size = blob.size;
  const m = /bytes=(\d*)-(\d*)/.exec(req.headers.get('range'));
  let start = 0, end = size - 1;
  if (m) {
    if (m[1]) { start = parseInt(m[1]); end = m[2] ? Math.min(parseInt(m[2]), size - 1) : size - 1; }
    else if (m[2]) { start = Math.max(0, size - parseInt(m[2])); }
  }
  if (start >= size) return new Response(null, { status: 416, headers: { 'Content-Range': `bytes */${size}` } });
  const part = blob.slice(start, end + 1);
  return new Response(part, {
    status: 206,
    headers: {
      'Content-Type': full.headers.get('Content-Type') || 'application/octet-stream',
      'Content-Range': `bytes ${start}-${end}/${size}`,
      'Content-Length': String(part.size),
      'Accept-Ranges': 'bytes',
    },
  });
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET' || !req.url.startsWith(self.location.origin)) return;
  e.respondWith((async () => {
    const cache = await caches.open(V);
    if (req.headers.get('range')) {
      try { return await rangeResponse(req, cache); }
      catch { return new Response('offline', { status: 503 }); }
    }
    // network-first: fresh whenever online; the cache is the offline fallback
    try {
      const res = await fetch(req);
      if (res.ok) cache.put(req, res.clone()).catch(() => {});
      return res;
    } catch {
      const hit = await cache.match(req, { ignoreSearch: true });
      if (hit) return hit;
      if (req.mode === 'navigate') {
        const shell = await cache.match('./index.html');
        if (shell) return shell;
      }
      return new Response('offline', { status: 503 });
    }
  })());
});
