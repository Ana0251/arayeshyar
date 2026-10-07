/**
 * Arayeshyar PWA Service Worker
 * v3: authenticated/management HTML is never served from cache.
 */
const CACHE_VERSION = 'arayeshyar-v3';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const OFFLINE_CACHE = `${CACHE_VERSION}-offline`;

const PRECACHE_URLS = [
    '/offline/',
    '/manifest.webmanifest',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',
    '/static/icons/apple-touch-icon.png',
    '/static/icons/favicon.ico',
];

self.addEventListener('install', function (event) {
    event.waitUntil(
        caches.open(OFFLINE_CACHE)
            .then(function (cache) {
                return Promise.all(PRECACHE_URLS.map(function (url) {
                    return cache.add(url).catch(function () { return null; });
                }));
            })
            .then(function () { return self.skipWaiting(); })
    );
});

self.addEventListener('activate', function (event) {
    event.waitUntil(
        caches.keys()
            .then(function (names) {
                return Promise.all(names
                    .filter(function (name) {
                        return name.startsWith('arayeshyar-') &&
                            name !== STATIC_CACHE && name !== OFFLINE_CACHE;
                    })
                    .map(function (name) { return caches.delete(name); }));
            })
            .then(function () { return self.clients.claim(); })
    );
});

self.addEventListener('fetch', function (event) {
    const request = event.request;
    if (request.method !== 'GET') return;

    const url = new URL(request.url);
    if (url.origin !== self.location.origin) return;

    // صفحات حساس/داینامیک همیشه مستقیماً از شبکه.
    const networkOnlyPrefixes = [
        '/admin/', '/control/', '/business/', '/booking/', '/customers/',
        '/accounts/', '/support/', '/api/', '/__debug__/', '/data/'
    ];
    if (networkOnlyPrefixes.some(function (prefix) { return url.pathname.startsWith(prefix); })) {
        event.respondWith(fetch(request));
        return;
    }

    // Static: network-first تا نسخه تازه فوراً اعمال شود.
    if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
        event.respondWith(
            fetch(request)
                .then(function (response) {
                    if (response && response.ok) {
                        const clone = response.clone();
                        caches.open(STATIC_CACHE).then(function (cache) { cache.put(request, clone); });
                    }
                    return response;
                })
                .catch(function () { return caches.match(request); })
        );
        return;
    }

    // HTML عمومی: network-first، فقط در حالت آفلاین fallback.
    const accept = request.headers.get('accept') || '';
    if (accept.includes('text/html')) {
        event.respondWith(
            fetch(request).catch(function () {
                return caches.match('/offline/');
            })
        );
        return;
    }

    event.respondWith(fetch(request));
});

self.addEventListener('message', function (event) {
    if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});
