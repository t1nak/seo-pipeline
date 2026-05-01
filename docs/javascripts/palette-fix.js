// Re-binds the palette toggle after StatiCrypt swaps the decrypted DOM in.
// Material's own init runs once against the StatiCrypt shell (no toggle present),
// so the inputs in the decrypted body never get listeners.
(function () {
  const KEY = "__palette";

  function applyFromStorage() {
    const raw = localStorage.getItem(KEY);
    if (!raw) return;
    const p = JSON.parse(raw);
    const scheme = p && p.color && p.color.scheme;
    if (!scheme) return;
    document.body.setAttribute("data-md-color-scheme", scheme);
    if (p.color.primary) document.body.setAttribute("data-md-color-primary", p.color.primary);
    if (p.color.accent) document.body.setAttribute("data-md-color-accent", p.color.accent);
    document.querySelectorAll('input[name="__palette"]').forEach((r, i) => {
      r.checked = i === p.index;
    });
  }

  function wire() {
    const radios = document.querySelectorAll('input[name="__palette"]');
    if (!radios.length) return false;
    radios.forEach((r, i) => {
      r.addEventListener("change", () => {
        if (!r.checked) return;
        const scheme = r.getAttribute("data-md-color-scheme");
        const primary = r.getAttribute("data-md-color-primary");
        const accent = r.getAttribute("data-md-color-accent");
        document.body.setAttribute("data-md-color-scheme", scheme);
        if (primary) document.body.setAttribute("data-md-color-primary", primary);
        if (accent) document.body.setAttribute("data-md-color-accent", accent);
        localStorage.setItem(KEY, JSON.stringify({ index: i, color: { scheme, primary, accent } }));
      });
    });
    return true;
  }

  function init() {
    applyFromStorage();
    if (wire()) return;
    const obs = new MutationObserver(() => {
      if (document.querySelector('input[name="__palette"]')) {
        applyFromStorage();
        wire();
        obs.disconnect();
      }
    });
    obs.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
