(function () {
  "use strict";

  var C = window.AD_CONFIG || {};
  var showPlaceholders = C.showPlaceholders !== false;

  function store(key, value) {
    try {
      if (value === undefined) return sessionStorage.getItem(key);
      sessionStorage.setItem(key, value);
    } catch (e) { return null; }
  }

  // innerHTML does not run <script> tags, so recreate them for pasted ad network snippets.
  function injectHTML(container, markup) {
    container.innerHTML = markup;
    container.querySelectorAll("script").forEach(function (old) {
      var s = document.createElement("script");
      for (var i = 0; i < old.attributes.length; i++) s.setAttribute(old.attributes[i].name, old.attributes[i].value);
      s.text = old.text;
      old.parentNode.replaceChild(s, old);
    });
  }

  function link(href, inner) {
    if (!href) return inner;
    return '<a href="' + encodeURI(href) + '" target="_blank" rel="sponsored noopener">' + inner + "</a>";
  }

  // ---------------------------------------------------------------- AdSense

  if (C.adsenseClient) {
    var s = document.createElement("script");
    s.async = true;
    s.crossOrigin = "anonymous";
    s.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + encodeURIComponent(C.adsenseClient);
    document.head.appendChild(s);
  }

  function fillSlots() {
    var slots = C.slots || {};
    document.querySelectorAll(".ad[data-ad]").forEach(function (box) {
      var name = box.getAttribute("data-ad");
      var id = slots[name];
      // Skip slots hidden at this screen size; AdSense cannot size an ad into a hidden box.
      var visible = box.getClientRects().length > 0;

      if (C.adsenseClient && id && visible) {
        var ins = document.createElement("ins");
        ins.className = "adsbygoogle";
        ins.setAttribute("data-ad-client", C.adsenseClient);
        ins.setAttribute("data-ad-slot", id);
        if (name.indexOf("rail") === 0) {
          var size = box.getAttribute("data-size").split("x");
          ins.style.cssText = "display:inline-block;width:" + size[0] + "px;height:" + size[1] + "px";
        } else {
          ins.style.display = "block";
          ins.setAttribute("data-ad-format", "auto");
          ins.setAttribute("data-full-width-responsive", "true");
        }
        var ph = box.querySelector(".ad-ph");
        if (ph) ph.remove();
        box.appendChild(ins);
        box.classList.add("is-filled");
        (window.adsbygoogle = window.adsbygoogle || []).push({});
      } else if (!showPlaceholders) {
        box.classList.add("is-empty");
      }
    });
  }

  // ---------------------------------------------------------------- video ad

  function setupVideo() {
    var v = C.video || {};
    var box = document.getElementById("video-ad");
    if (!box || !v.enabled || store("uc-video-closed")) return;
    if (!v.src && !v.html && !showPlaceholders) return;

    var body = box.querySelector(".video-ad-body");
    var shown = false;

    function show() {
      if (shown || store("uc-video-closed")) return;
      shown = true;
      if (v.html) injectHTML(body, v.html);
      else if (v.src) {
        body.innerHTML = link(v.link, '<video src="' + encodeURI(v.src) + '" muted autoplay loop playsinline></video>');
      }
      box.hidden = false;
      document.body.classList.add("has-video-ad");
    }

    // Wait until the converter has scrolled out of view, so the player never covers it
    // (or the top of the sticky vertical banner, which starts level with the converter).
    var converter = document.getElementById("converter") || document.querySelector("main > :first-child");
    setTimeout(function () {
      if (!converter || !("IntersectionObserver" in window)) return show();
      new IntersectionObserver(function (entries, obs) {
        if (!entries[0].isIntersecting) { obs.disconnect(); show(); }
      }).observe(converter);
    }, (v.delaySeconds || 0) * 1000);

    box.querySelector("[data-close-video]").addEventListener("click", function () {
      box.hidden = true;
      body.innerHTML = "";
      document.body.classList.remove("has-video-ad");
      store("uc-video-closed", "1");
    });
  }

  // ---------------------------------------------------------------- full-screen ad

  function setupInterstitial() {
    var cfg = C.interstitial || {};
    var modal = document.getElementById("interstitial");
    if (!modal || !cfg.enabled) return;
    if (!cfg.image && !cfg.html && !showPlaceholders) return;

    var body = modal.querySelector(".interstitial-body");
    var btn = modal.querySelector("[data-close-interstitial]");
    var pending = null;

    function open(href) {
      pending = href;
      if (cfg.html) injectHTML(body, cfg.html);
      else if (cfg.image) body.innerHTML = link(cfg.link, '<img src="' + encodeURI(cfg.image) + '" alt="Advertisement">');
      modal.hidden = false;
      document.body.classList.add("has-interstitial");
      store("uc-interstitial-shown", "1");
      btn.focus();
    }

    function close() {
      modal.hidden = true;
      document.body.classList.remove("has-interstitial");
      if (pending) location.href = pending;
    }

    btn.addEventListener("click", close);
    modal.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { e.preventDefault(); close(); return; }
      if (e.key === "Tab") {
        // Keep focus inside the dialog.
        var items = modal.querySelectorAll("button, a[href], iframe, [tabindex]:not([tabindex='-1'])");
        var first = items[0], last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });

    document.addEventListener("click", function (e) {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var a = e.target.closest && e.target.closest("a[href]");
      if (!a || a.target === "_blank" || a.hasAttribute("download") || modal.contains(a)) return;
      var url = new URL(a.href, location.href);
      if (url.origin !== location.origin) return;
      if (url.pathname === location.pathname && url.search === location.search && url.hash) return;

      var count = (parseInt(store("uc-navs"), 10) || 0) + 1;
      store("uc-navs", String(count));
      if (count >= (cfg.onNavigation || 2) && !store("uc-interstitial-shown")) {
        e.preventDefault();
        open(url.href);
      }
    });
  }

  function init() {
    fillSlots();
    setupVideo();
    setupInterstitial();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
