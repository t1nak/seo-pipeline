/* Simple lightbox for images marked with class "zoomable".
   Click opens a full-screen modal with the image scaled to viewport.
   Wheel / pinch zoom works inside the modal because the image is a
   plain <img> with no event blocking. Esc or click outside closes. */
(function () {
  function initLightbox() {
    var imgs = document.querySelectorAll("img.zoomable");
    if (!imgs.length) return;
    imgs.forEach(function (img) {
      if (img.dataset.lbInit) return;
      img.dataset.lbInit = "1";
      img.style.cursor = "zoom-in";
      img.addEventListener("click", function (e) {
        e.preventDefault();
        openLightbox(img.src, img.alt || "");
      });
    });
  }

  function openLightbox(src, alt) {
    var overlay = document.createElement("div");
    overlay.className = "lb-overlay";
    overlay.innerHTML =
      '<button class="lb-close" aria-label="Close">&times;</button>' +
      '<div class="lb-stage"><img class="lb-img" src="' +
      src +
      '" alt="' +
      alt.replace(/"/g, "&quot;") +
      '"></div>' +
      '<div class="lb-hint">Maus-Rad zum Zoomen, Klick außerhalb zum Schließen</div>';
    document.body.appendChild(overlay);
    document.body.style.overflow = "hidden";

    var img = overlay.querySelector(".lb-img");
    var stage = overlay.querySelector(".lb-stage");
    var scale = 1;

    function close() {
      overlay.remove();
      document.body.style.overflow = "";
      document.removeEventListener("keydown", onKey);
    }
    function onKey(e) {
      if (e.key === "Escape") close();
      if (e.key === "+" || e.key === "=") { scale = Math.min(scale * 1.2, 6); applyScale(); }
      if (e.key === "-") { scale = Math.max(scale / 1.2, 0.5); applyScale(); }
      if (e.key === "0") { scale = 1; applyScale(); }
    }
    function applyScale() {
      img.style.transform = "scale(" + scale + ")";
    }

    overlay.addEventListener("click", function (e) {
      if (e.target === overlay || e.target.classList.contains("lb-close") || e.target.classList.contains("lb-stage") || e.target.classList.contains("lb-hint")) {
        close();
      }
    });
    overlay.addEventListener("wheel", function (e) {
      e.preventDefault();
      var delta = e.deltaY < 0 ? 1.1 : 1 / 1.1;
      scale = Math.max(0.5, Math.min(6, scale * delta));
      applyScale();
    }, { passive: false });
    document.addEventListener("keydown", onKey);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initLightbox);
  } else {
    initLightbox();
  }
  // Re-init on Material instant navigation
  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(initLightbox);
  }
})();
