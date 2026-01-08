/**
 * Tile Cache Service Worker
 * Caches map tiles from OpenFreeMap for offline use
 */

const CACHE_NAME = 'dashy-map-tiles-v1';
const TILE_HOSTS = ['tiles.openfreemap.org'];
const MAX_CACHE_SIZE = 2000; // Max tiles to cache
const TRIM_INTERVAL = 60000; // Only trim cache every 60 seconds

// Debug mode - can be set via message from main thread
let _debug = false;
let _lastTrimTime = 0;

function debugLog(...args) {
    if (_debug) console.log(...args);
}

// Listen for debug toggle from main thread
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SET_DEBUG') {
        _debug = event.data.value;
    }
});

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName.startsWith('dashy-map-tiles-') && cacheName !== CACHE_NAME) {
                        debugLog('[TileCache SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Only cache tile requests from OpenFreeMap
    const isTileRequest = TILE_HOSTS.some(host => url.hostname.includes(host));
    if (!isTileRequest) return;

    event.respondWith(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.match(event.request).then((cachedResponse) => {
                if (cachedResponse) {
                    // Return cached, but also update cache in background
                    fetchAndCache(event.request, cache);
                    return cachedResponse;
                }

                return fetchAndCache(event.request, cache);
            });
        })
    );
});

async function fetchAndCache(request, cache) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
            trimCache(cache);
        }
        return networkResponse;
    } catch (e) {
        // Return cached version if offline
        const cached = await cache.match(request);
        if (cached) return cached;
        throw e;
    }
}

async function trimCache(cache) {
    // Only trim every TRIM_INTERVAL to avoid constant overhead
    const now = Date.now();
    if (now - _lastTrimTime < TRIM_INTERVAL) {
        return;
    }
    _lastTrimTime = now;

    const keys = await cache.keys();
    if (keys.length > MAX_CACHE_SIZE) {
        // Delete oldest entries
        const toDelete = keys.slice(0, keys.length - MAX_CACHE_SIZE);
        for (const key of toDelete) {
            await cache.delete(key);
        }
        debugLog('[TileCache SW] Trimmed', toDelete.length, 'old tiles');
    }
}
