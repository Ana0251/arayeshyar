/**
 * Service Worker برای PWA آرایشیار.
 *
 * ─── استراتژی: ───
 * - Static assets → Cache First
 * - HTML → Network First + Fallback
 * - Offline → صفحه‌ی offline
 */

const CACHE_VERSION = 'arayeshyar-v1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;

// ═══════════════════════════════════════════════════════════════
//  Pre-cache URLs
// ═══════════════════════════════════════════════════════════════

const PRECACHE_URLS = [
    '/',
    '/offline/',
    '/manifest.webmanifest',
    '/static/css/tailwind.css',
    '/static/js/jalali.js',
    '/static/js/booking-app.js',
    '/static/js/booking-datepicker.js',
    '/static/js/time-picker.js',
    '/static/js/date-picker.js',
    '/static/js/common.js',
    '/static/js/avatar-preview.js',
    '/static/js/register-activity.js',
    '/static/js/register-services.js',
    '/static/js/register-stations.js',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',
    '/static/icons/apple-touch-icon.png',
    '/static/icons/favicon.ico',
];

// ═══════════════════════════════════════════════════════════════
//  Install
// ═══════════════════════════════════════════════════════════════

self.addEventListener('install', function (event) {
    console.log('[SW] Installing...');

    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(function (cache) {
                console.log('[SW] Pre-caching static assets');

                return Promise.all(
                    PRECACHE_URLS.map(function (url) {
                        return cache.add(url).catch(function (err) {
                            console.warn('[SW] Failed to cache:', url, err);
                        });
                    })
                );
            })
            .then(function () {
                return self.skipWaiting();
            })
    );
});

// ═══════════════════════════════════════════════════════════════
//  Activate
// ═══════════════════════════════════════════════════════════════

self.addEventListener('activate', function (event) {
    console.log('[SW] Activating...');

    event.waitUntil(
        caches.keys()
            .then(function (cacheNames) {
                return Promise.all(
                    cacheNames
                        .filter(function (name) {
                            return name !== STATIC_CACHE && name !== DYNAMIC_CACHE;
                        })
                        .map(function (name) {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(function () {
                return self.clients.claim();
            })
    );
});

// ═══════════════════════════════════════════════════════════════
//  Fetch
// ═══════════════════════════════════════════════════════════════

self.addEventListener('fetch', function (event) {
    const request = event.request;
    const url = new URL(request.url);

    // ─── فقط GET ───
    if (request.method !== 'GET') return;

    // ─── فقط same-origin ───
    if (url.origin !== location.origin) return;

    // ─── Admin, API, Debug → Network Only ───
    if (
        url.pathname.startsWith('/admin/') ||
        url.pathname.startsWith('/api/') ||
        url.pathname.startsWith('/__debug__/') ||
        url.pathname.startsWith('/data/')
    ) {
        return;
    }

    // ─── Static assets → Cache First ───
    if (
        url.pathname.startsWith('/static/') ||
        url.pathname.startsWith('/media/')
    ) {
        event.respondWith(
            caches.match(request).then(function (cached) {
                if (cached) return cached;

                return fetch(request).then(function (response) {
                    if (response && response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(STATIC_CACHE).then(function (cache) {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                });
            })
        );
        return;
    }

    // ─── HTML → Network First + Fallback ───
    const acceptHeader = request.headers.get('accept') || '';
    if (acceptHeader.includes('text/html')) {
        event.respondWith(
            fetch(request)
                .then(function (response) {
                    if (response && response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(DYNAMIC_CACHE).then(function (cache) {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                })
                .catch(function () {
                    return caches.match(request).then(function (cached) {
                        return cached || caches.match('/offline/');
                    });
                })
        );
        return;
    }

    // ─── بقیه → Network ───
    event.respondWith(fetch(request));
});

// ═══════════════════════════════════════════════════════════════
//  Message
// ═══════════════════════════════════════════════════════════════

self.addEventListener('message', function (event) {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});