// KM6 SC2 currently uses software video decoding; retain GPU page rendering.
user_pref("media.av1.enabled", false);
// Internal eMMC can cache websites persistently instead of re-fetching them.
user_pref("browser.cache.disk.enable", true);
user_pref("browser.cache.disk.capacity", 131072);
user_pref("browser.cache.memory.enable", true);
user_pref("browser.cache.memory.capacity", 65536);
user_pref("browser.startup.page", 3);
