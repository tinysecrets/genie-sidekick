// Minimal service worker for "Add to Home Screen" install prompt.
// Network-first; we don't aggressively cache the SPA shell to avoid stale builds.
self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  // Pass-through; required by some browsers to recognize as installable.
  return;
});
