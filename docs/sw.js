// 연락처QR 서비스 워커 — 정적 자산 캐시 전용 (페이지/QR은 항상 네트워크)
var CACHE = 'contact-qr-static-v1';
var ASSETS = [
  'icon-192.png',
  'icon-512.png',
  'icon-maskable.png',
  'qrcode.min.js'
];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE).then(function (c) {
      return Promise.all(ASSETS.map(function (a) {
        return c.add(new Request(a, { cache: 'reload' }));
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== CACHE; })
        .map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;
  var url = new URL(e.request.url);
  if (url.origin !== location.origin) return;
  // 파일명 기준 비교 (하위 경로 배포 대응)
  var file = url.pathname.split('/').pop();
  if (ASSETS.indexOf(file) === -1) return;  // 나머지는 전부 네트워크로 통과
  e.respondWith(
    caches.match(e.request).then(function (hit) { return hit || fetch(e.request); })
  );
});
