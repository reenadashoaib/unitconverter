(function () {
  "use strict";

  var root = document.getElementById("converter");
  if (!root || !window.UNIT_DATA) return;

  var el = {
    category: document.getElementById("cv-category"),
    value: document.getElementById("cv-value"),
    from: document.getElementById("cv-from"),
    to: document.getElementById("cv-to"),
    swap: document.getElementById("cv-swap"),
    num: document.getElementById("cv-num"),
    unit: document.getElementById("cv-unit"),
    formula: document.getElementById("cv-formula"),
    copy: document.getElementById("cv-copy"),
    all: document.getElementById("cv-all"),
    allTitle: document.getElementById("all-title")
  };

  var slug = root.getAttribute("data-category");
  var cat = window.UNIT_DATA[slug];

  // Temperature has no linear factors, so it goes through kelvin.
  var TO_K = {
    c: function (v) { return v + 273.15; },
    f: function (v) { return (v - 32) * 5 / 9 + 273.15; },
    k: function (v) { return v; },
    r: function (v) { return v * 5 / 9; }
  };
  var FROM_K = {
    c: function (k) { return k - 273.15; },
    f: function (k) { return (k - 273.15) * 9 / 5 + 32; },
    k: function (k) { return k; },
    r: function (k) { return k * 9 / 5; }
  };

  function find(id) {
    for (var i = 0; i < cat.units.length; i++) if (cat.units[i].id === id) return cat.units[i];
    return null;
  }

  function convert(v, from, to) {
    if (slug === "temperature") return FROM_K[to](TO_K[from](v));
    return v * find(from).f / find(to).f;
  }

  var numberFormat = new Intl.NumberFormat("en-US", { maximumSignificantDigits: 10 });

  // Mirrors fmt() in tools/build.py.
  function fmt(x) {
    if (!isFinite(x)) return "–";
    if (x === 0) return "0";
    var a = Math.abs(x);
    if (a >= 1e15 || a < 1e-6) {
      var exp = Math.floor(Math.log10(a));
      var mant = parseFloat((x / Math.pow(10, exp)).toPrecision(6));
      return mant + " × 10<sup>" + exp + "</sup>";
    }
    return numberFormat.format(parseFloat(x.toPrecision(12))).replace("-", "−");
  }

  function plain(x) {
    return fmt(x).replace(/<sup>/, "^").replace(/<\/sup>/, "");
  }

  function name(u, v) { return v === 1 ? u.one : u.many; }

  function parse(s) {
    s = String(s).trim().replace(/,/g, "").replace(/−/g, "-");
    if (s === "" || s === "-" || s === ".") return NaN;
    return Number(s);
  }

  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

  function fillSelects(from, to) {
    var opts = cat.units.map(function (u) {
      return '<option value="' + u.id + '">' + cap(u.one) + " (" + u.sym + ")</option>";
    }).join("");
    el.from.innerHTML = opts;
    el.to.innerHTML = opts;
    el.from.value = from;
    el.to.value = to;
  }

  var lastTicks = 0;

  function render() {
    var v = parse(el.value.value);
    var from = find(el.from.value), to = find(el.to.value);
    var valid = !isNaN(v);
    root.classList.toggle("is-invalid", !valid && el.value.value.trim() !== "");

    if (!valid) {
      el.num.textContent = "–";
      el.unit.textContent = to.many;
      el.all.innerHTML = "";
      return;
    }

    var res = convert(v, from.id, to.id);
    el.num.innerHTML = fmt(res);
    el.unit.textContent = name(to, res);
    var one = convert(1, from.id, to.id);
    el.formula.innerHTML = "1 " + from.one + " = " + fmt(one) + " " + name(to, one);

    el.all.innerHTML = cat.units.map(function (u) {
      var r = convert(v, from.id, u.id);
      var cur = u.id === to.id ? ' class="is-current"' : "";
      return "<tr" + cur + '><th scope="row">' + cap(u.many) + "</th><td>" + fmt(r) +
        ' <span class="sym">' + u.sym + "</span></td></tr>";
    }).join("");

    // The ruler ticks slide in proportion to the size of the answer.
    var shift = Math.log10(Math.abs(res) || 1) * 48;
    if (isFinite(shift) && shift !== lastTicks) {
      root.style.setProperty("--tick-shift", shift.toFixed(1) + "px");
      lastTicks = shift;
    }
  }

  function syncUrl() {
    if (!window.history || !history.replaceState) return;
    var params = new URLSearchParams(location.search);
    if (el.category) params.set("measure", slug);
    params.set("from", el.from.value);
    params.set("to", el.to.value);
    params.set("v", el.value.value.trim());
    history.replaceState(null, "", location.pathname + "?" + params.toString());
  }

  function update() { render(); syncUrl(); }

  function setCategory(s, from, to) {
    slug = s;
    cat = window.UNIT_DATA[s];
    root.setAttribute("data-category", s);
    fillSelects(find(from) ? from : cat.default[0], find(to) ? to : cat.default[1]);
    if (el.allTitle) el.allTitle.textContent = "The same value in every " + cat.noun + " unit";
  }

  // Restore state from the address bar (shared links, popular-conversion links).
  var q = new URLSearchParams(location.search);
  if (el.category && q.get("measure") && window.UNIT_DATA[q.get("measure")]) {
    el.category.value = q.get("measure");
    setCategory(q.get("measure"), q.get("from"), q.get("to"));
  } else if (q.get("from") || q.get("to")) {
    setCategory(slug, q.get("from"), q.get("to"));
  }
  if (q.get("v") !== null && q.get("v") !== "") el.value.value = q.get("v");

  el.value.addEventListener("input", update);
  el.from.addEventListener("change", update);
  el.to.addEventListener("change", update);
  el.swap.addEventListener("click", function () {
    var f = el.from.value;
    el.from.value = el.to.value;
    el.to.value = f;
    el.swap.classList.toggle("is-flipped");
    update();
  });
  if (el.category) {
    el.category.addEventListener("change", function () {
      setCategory(el.category.value);
      update();
    });
  }

  el.copy.addEventListener("click", function () {
    var v = parse(el.value.value);
    if (isNaN(v)) return;
    var from = find(el.from.value), to = find(el.to.value);
    var res = convert(v, from.id, to.id);
    var text = el.value.value.trim() + " " + from.sym + " = " + plain(res) + " " + to.sym;
    var done = function () {
      el.copy.textContent = "Copied";
      setTimeout(function () { el.copy.textContent = "Copy result"; }, 1600);
    };
    if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, function () {});
  });

  render();
})();
