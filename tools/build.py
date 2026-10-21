#!/usr/bin/env python3
"""Generate the static site in public/ from the unit data and page content below.

Run:  python3 tools/build.py

Everything in public/ except assets/css, assets/js/converter.js, assets/js/ads.js,
assets/js/ads-config.js, ads.txt, robots.txt and _headers is written by this script,
so edit the content here rather than in the generated HTML.
"""

import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

SITE = {
    "name": "Unit Converter",
    # Your live address, no trailing slash. Used for canonical links and sitemap.xml.
    "url": "https://example.com",
    "email": "contact@example.com",
}

# Each unit: (id, singular, plural, symbol, factor to the category's base unit).
# Temperature has no factors; it is converted through kelvin in code.
CATEGORIES = [
    {
        "slug": "length",
        "name": "Length",
        "noun": "length",
        "units": [
            ("mm", "millimeter", "millimeters", "mm", 0.001),
            ("cm", "centimeter", "centimeters", "cm", 0.01),
            ("m", "meter", "meters", "m", 1),
            ("km", "kilometer", "kilometers", "km", 1000),
            ("um", "micrometer", "micrometers", "µm", 1e-6),
            ("in", "inch", "inches", "in", 0.0254),
            ("ft", "foot", "feet", "ft", 0.3048),
            ("yd", "yard", "yards", "yd", 0.9144),
            ("mi", "mile", "miles", "mi", 1609.344),
            ("nmi", "nautical mile", "nautical miles", "nmi", 1852),
        ],
        "default": ("in", "cm"),
        "popular": [("in", "cm"), ("cm", "in"), ("ft", "m"), ("m", "ft"),
                    ("km", "mi"), ("mi", "km"), ("mm", "in"), ("yd", "m")],
        "intro": "Convert between metric lengths like millimeters, meters and kilometers "
                 "and imperial lengths like inches, feet, yards and miles. Every imperial "
                 "length is defined from the meter, so these conversions are exact.",
        "faq": [
            ("How many centimeters are in an inch?",
             "Exactly 2.54. Since 1959 the international inch has been defined as 25.4 millimeters."),
            ("How many feet are in a meter?",
             "About 3.28084 feet. A foot is exactly 0.3048 meters."),
            ("What is the difference between a mile and a nautical mile?",
             "A mile is 1,609.344 meters. A nautical mile is 1,852 meters and is used for sea and air navigation."),
        ],
    },
    {
        "slug": "weight",
        "name": "Weight",
        "noun": "weight",
        "units": [
            ("mg", "milligram", "milligrams", "mg", 1e-6),
            ("g", "gram", "grams", "g", 0.001),
            ("kg", "kilogram", "kilograms", "kg", 1),
            ("t", "metric ton", "metric tons", "t", 1000),
            ("oz", "ounce", "ounces", "oz", 0.028349523125),
            ("lb", "pound", "pounds", "lb", 0.45359237),
            ("st", "stone", "stone", "st", 6.35029318),
            ("ton", "US ton", "US tons", "ton", 907.18474),
            ("lt", "UK ton", "UK tons", "long ton", 1016.0469088),
        ],
        "default": ("lb", "kg"),
        "popular": [("lb", "kg"), ("kg", "lb"), ("oz", "g"), ("g", "oz"),
                    ("st", "kg"), ("kg", "st"), ("t", "ton"), ("mg", "g")],
        "intro": "Convert weight and mass between grams, kilograms and metric tons and "
                 "ounces, pounds, stone and tons. The pound is defined as exactly "
                 "0.45359237 kilograms.",
        "faq": [
            ("How many pounds are in a kilogram?",
             "About 2.20462 pounds. One pound is exactly 0.45359237 kilograms."),
            ("How many pounds are in a stone?",
             "14 pounds, or about 6.35 kilograms. Stone is still used for body weight in the UK and Ireland."),
            ("Is a metric ton the same as a ton?",
             "No. A metric ton is 1,000 kg. A US ton is 2,000 pounds (907.18 kg) and a UK ton is 2,240 pounds (1,016.05 kg)."),
        ],
    },
    {
        "slug": "temperature",
        "name": "Temperature",
        "noun": "temperature",
        "units": [
            ("c", "degree Celsius", "degrees Celsius", "°C", None),
            ("f", "degree Fahrenheit", "degrees Fahrenheit", "°F", None),
            ("k", "kelvin", "kelvins", "K", None),
            ("r", "degree Rankine", "degrees Rankine", "°R", None),
        ],
        "default": ("f", "c"),
        "example": (100, "c", "f"),
        "popular": [("f", "c"), ("c", "f"), ("c", "k"), ("k", "c"), ("f", "k"), ("k", "f")],
        "intro": "Convert temperatures between Celsius, Fahrenheit, kelvin and Rankine. "
                 "Temperature scales have different zero points, so they are not simple "
                 "multiples of each other.",
        "faq": [
            ("How do I convert Fahrenheit to Celsius?",
             "Subtract 32, then multiply by 5/9. For example, 68 °F is (68 − 32) × 5/9 = 20 °C."),
            ("At what temperature are Celsius and Fahrenheit equal?",
             "At −40. Minus 40 °C is exactly minus 40 °F."),
            ("Why is kelvin written without a degree sign?",
             "Kelvin is an absolute scale that starts at absolute zero (−273.15 °C), so its unit is just K."),
        ],
    },
    {
        "slug": "volume",
        "name": "Volume",
        "noun": "volume",
        "units": [
            ("ml", "milliliter", "milliliters", "mL", 0.001),
            ("l", "liter", "liters", "L", 1),
            ("m3", "cubic meter", "cubic meters", "m³", 1000),
            ("tsp", "teaspoon (US)", "teaspoons (US)", "tsp", 0.00492892159375),
            ("tbsp", "tablespoon (US)", "tablespoons (US)", "tbsp", 0.01478676478125),
            ("floz", "fluid ounce (US)", "fluid ounces (US)", "fl oz", 0.0295735295625),
            ("cup", "cup (US)", "cups (US)", "cup", 0.2365882365),
            ("pt", "pint (US)", "pints (US)", "pt", 0.473176473),
            ("qt", "quart (US)", "quarts (US)", "qt", 0.946352946),
            ("gal", "gallon (US)", "gallons (US)", "gal", 3.785411784),
            ("ipt", "pint (UK)", "pints (UK)", "UK pt", 0.56826125),
            ("igal", "gallon (UK)", "gallons (UK)", "UK gal", 4.54609),
            ("in3", "cubic inch", "cubic inches", "in³", 0.016387064),
            ("ft3", "cubic foot", "cubic feet", "ft³", 28.316846592),
        ],
        "default": ("gal", "l"),
        "popular": [("gal", "l"), ("l", "gal"), ("cup", "ml"), ("ml", "cup"),
                    ("floz", "ml"), ("tbsp", "ml"), ("tsp", "ml"), ("igal", "l")],
        "intro": "Convert liquid and dry volumes between milliliters, liters and cubic "
                 "meters and US and UK cooking and trade measures. US and UK gallons and "
                 "pints are different sizes, so both are listed.",
        "faq": [
            ("Is a US gallon the same as a UK gallon?",
             "No. A US gallon is 3.785 liters and a UK (imperial) gallon is 4.546 liters, about 20% larger."),
            ("How many cups are in a liter?",
             "About 4.23 US cups. This converter uses the US customary cup of 236.59 mL; nutrition labels round it to 240 mL."),
            ("How many milliliters are in a teaspoon?",
             "A US teaspoon is about 4.93 mL. Recipes outside the US often use a metric teaspoon of exactly 5 mL."),
        ],
    },
    {
        "slug": "area",
        "name": "Area",
        "noun": "area",
        "units": [
            ("mm2", "square millimeter", "square millimeters", "mm²", 1e-6),
            ("cm2", "square centimeter", "square centimeters", "cm²", 1e-4),
            ("m2", "square meter", "square meters", "m²", 1),
            ("ha", "hectare", "hectares", "ha", 1e4),
            ("km2", "square kilometer", "square kilometers", "km²", 1e6),
            ("in2", "square inch", "square inches", "in²", 0.00064516),
            ("ft2", "square foot", "square feet", "ft²", 0.09290304),
            ("yd2", "square yard", "square yards", "yd²", 0.83612736),
            ("ac", "acre", "acres", "ac", 4046.8564224),
            ("mi2", "square mile", "square miles", "mi²", 2589988.110336),
        ],
        "default": ("ft2", "m2"),
        "popular": [("ft2", "m2"), ("m2", "ft2"), ("ac", "ha"), ("ha", "ac"),
                    ("km2", "mi2"), ("mi2", "km2"), ("ac", "ft2"), ("cm2", "in2")],
        "intro": "Convert floor space, land and map areas between square meters, hectares "
                 "and square kilometers and square feet, acres and square miles.",
        "faq": [
            ("How many square feet are in a square meter?",
             "About 10.764 square feet."),
            ("How many acres are in a hectare?",
             "About 2.471 acres. A hectare is 10,000 square meters."),
            ("How big is an acre?",
             "43,560 square feet, or about 4,047 square meters."),
        ],
    },
    {
        "slug": "speed",
        "name": "Speed",
        "noun": "speed",
        "units": [
            ("ms", "meter per second", "meters per second", "m/s", 1),
            ("kmh", "kilometer per hour", "kilometers per hour", "km/h", 1 / 3.6),
            ("mph", "mile per hour", "miles per hour", "mph", 0.44704),
            ("kn", "knot", "knots", "kn", 1852 / 3600),
            ("fts", "foot per second", "feet per second", "ft/s", 0.3048),
        ],
        "default": ("mph", "kmh"),
        "popular": [("mph", "kmh"), ("kmh", "mph"), ("kn", "kmh"), ("kmh", "kn"),
                    ("ms", "kmh"), ("kn", "mph")],
        "intro": "Convert speeds between kilometers per hour, miles per hour, meters per "
                 "second, knots and feet per second.",
        "faq": [
            ("How do I convert km/h to mph?",
             "Divide by 1.609344. For example, 100 km/h is about 62.14 mph."),
            ("What is a knot?",
             "One nautical mile per hour, which is 1.852 km/h or about 1.151 mph."),
            ("How do I convert m/s to km/h?",
             "Multiply by 3.6. For example, 10 m/s is 36 km/h."),
        ],
    },
    {
        "slug": "time",
        "name": "Time",
        "noun": "time",
        "units": [
            ("ns", "nanosecond", "nanoseconds", "ns", 1e-9),
            ("us", "microsecond", "microseconds", "µs", 1e-6),
            ("msec", "millisecond", "milliseconds", "ms", 1e-3),
            ("s", "second", "seconds", "s", 1),
            ("min", "minute", "minutes", "min", 60),
            ("h", "hour", "hours", "h", 3600),
            ("d", "day", "days", "d", 86400),
            ("wk", "week", "weeks", "wk", 604800),
            ("mo", "month", "months", "mo", 2629746),
            ("yr", "year", "years", "yr", 31556952),
        ],
        "default": ("h", "min"),
        "popular": [("h", "min"), ("min", "s"), ("d", "h"), ("wk", "d"),
                    ("yr", "d"), ("s", "msec"), ("mo", "wk"), ("yr", "wk")],
        "intro": "Convert durations from nanoseconds to years. Months and years use "
                 "average Gregorian calendar lengths, so they are best for estimates.",
        "faq": [
            ("How many seconds are in a day?",
             "86,400 seconds: 24 hours × 60 minutes × 60 seconds."),
            ("How long is a month here?",
             "An average Gregorian month of 30.436875 days. A year is 365.2425 days, which accounts for leap years."),
            ("How many hours are in a week?",
             "168 hours."),
        ],
    },
    {
        "slug": "data",
        "name": "Data",
        "noun": "data size",
        "units": [
            ("bit", "bit", "bits", "bit", 0.125),
            ("B", "byte", "bytes", "B", 1),
            ("kB", "kilobyte", "kilobytes", "kB", 1e3),
            ("MB", "megabyte", "megabytes", "MB", 1e6),
            ("GB", "gigabyte", "gigabytes", "GB", 1e9),
            ("TB", "terabyte", "terabytes", "TB", 1e12),
            ("PB", "petabyte", "petabytes", "PB", 1e15),
            ("KiB", "kibibyte", "kibibytes", "KiB", 1024),
            ("MiB", "mebibyte", "mebibytes", "MiB", 1024 ** 2),
            ("GiB", "gibibyte", "gibibytes", "GiB", 1024 ** 3),
            ("TiB", "tebibyte", "tebibytes", "TiB", 1024 ** 4),
            ("Mbit", "megabit", "megabits", "Mb", 1.25e5),
            ("Gbit", "gigabit", "gigabits", "Gb", 1.25e8),
        ],
        "default": ("GB", "MB"),
        "popular": [("GB", "MB"), ("MB", "kB"), ("TB", "GB"), ("GB", "GiB"),
                    ("TB", "TiB"), ("Mbit", "MB"), ("MB", "Mbit"), ("Gbit", "GB")],
        "intro": "Convert file sizes and storage between bits, bytes, kilobytes, megabytes, "
                 "gigabytes and terabytes, in both decimal units (1 kB = 1,000 bytes) and "
                 "binary units (1 KiB = 1,024 bytes).",
        "faq": [
            ("What is the difference between a kB and a KiB?",
             "A kilobyte (kB) is 1,000 bytes. A kibibyte (KiB) is 1,024 bytes. That is why a 1 TB drive shows up as about 931 GiB."),
            ("How do I turn internet speed into download speed?",
             "Divide megabits by 8 to get megabytes. A 100 Mbps connection moves at most 12.5 MB per second."),
            ("How many gigabytes are in a terabyte?",
             "1,000 gigabytes, or 1,024 gibibytes in a tebibyte."),
        ],
    },
    {
        "slug": "pressure",
        "name": "Pressure",
        "noun": "pressure",
        "units": [
            ("pa", "pascal", "pascals", "Pa", 1),
            ("kpa", "kilopascal", "kilopascals", "kPa", 1e3),
            ("mpa", "megapascal", "megapascals", "MPa", 1e6),
            ("bar", "bar", "bar", "bar", 1e5),
            ("mbar", "millibar", "millibars", "mbar", 100),
            ("atm", "atmosphere", "atmospheres", "atm", 101325),
            ("psi", "pound per square inch", "pounds per square inch", "psi", 6894.757293168),
            ("mmhg", "millimeter of mercury", "millimeters of mercury", "mmHg", 133.322387415),
            ("inhg", "inch of mercury", "inches of mercury", "inHg", 3386.389),
            ("torr", "torr", "torr", "Torr", 101325 / 760),
        ],
        "default": ("psi", "bar"),
        "popular": [("psi", "bar"), ("bar", "psi"), ("psi", "kpa"), ("kpa", "psi"),
                    ("atm", "pa"), ("mmhg", "kpa"), ("inhg", "mbar"), ("bar", "atm")],
        "intro": "Convert pressure between pascals, bar and atmospheres and psi, inches and "
                 "millimeters of mercury, for tires, weather, diving and engineering.",
        "faq": [
            ("How many psi are in a bar?",
             "About 14.504 psi."),
            ("What is standard atmospheric pressure?",
             "101,325 pascals, which is 1.01325 bar, about 14.696 psi or 760 mmHg."),
            ("Is a torr the same as a millimeter of mercury?",
             "Almost. A torr is exactly 1/760 of an atmosphere; 1 mmHg is about 1.00000014 torr."),
        ],
    },
    {
        "slug": "energy",
        "name": "Energy",
        "noun": "energy",
        "units": [
            ("j", "joule", "joules", "J", 1),
            ("kj", "kilojoule", "kilojoules", "kJ", 1e3),
            ("cal", "calorie", "calories", "cal", 4.184),
            ("kcal", "kilocalorie", "kilocalories", "kcal", 4184),
            ("wh", "watt-hour", "watt-hours", "Wh", 3600),
            ("kwh", "kilowatt-hour", "kilowatt-hours", "kWh", 3.6e6),
            ("btu", "British thermal unit", "British thermal units", "BTU", 1055.05585262),
            ("ftlb", "foot-pound", "foot-pounds", "ft·lbf", 1.3558179483314004),
            ("ev", "electronvolt", "electronvolts", "eV", 1.602176634e-19),
        ],
        "default": ("kcal", "kj"),
        "popular": [("kcal", "kj"), ("kj", "kcal"), ("kwh", "j"), ("btu", "kwh"),
                    ("kwh", "btu"), ("cal", "j"), ("wh", "j"), ("ftlb", "j")],
        "intro": "Convert energy between joules, calories, kilocalories, watt-hours, "
                 "kilowatt-hours, BTU and electronvolts, for food labels, electricity bills "
                 "and physics.",
        "faq": [
            ("Is a food Calorie the same as a calorie?",
             "No. The Calorie on food labels is a kilocalorie: 1,000 calories, or 4,184 joules."),
            ("How many joules are in a kilowatt-hour?",
             "3,600,000 joules (3.6 MJ). Electricity is billed in kilowatt-hours."),
            ("What is a BTU?",
             "The energy needed to heat one pound of water by 1 °F, about 1,055 joules. It is used to rate heaters and air conditioners."),
        ],
    },
]

BY_SLUG = {c["slug"]: c for c in CATEGORIES}
HOME_DEFAULT = "length"


# ---------------------------------------------------------------- conversion

def unit(cat, uid):
    for u in cat["units"]:
        if u[0] == uid:
            return u
    raise KeyError(uid)


TEMP_TO_K = {"c": lambda v: v + 273.15, "f": lambda v: (v - 32) * 5 / 9 + 273.15,
             "k": lambda v: v, "r": lambda v: v * 5 / 9}
TEMP_FROM_K = {"c": lambda k: k - 273.15, "f": lambda k: (k - 273.15) * 9 / 5 + 32,
               "k": lambda k: k, "r": lambda k: k * 9 / 5}


def convert(cat, value, frm, to):
    if cat["slug"] == "temperature":
        return TEMP_FROM_K[to](TEMP_TO_K[frm](value))
    return value * unit(cat, frm)[4] / unit(cat, to)[4]


def fmt(x):
    """Same rules as fmt() in converter.js: 10 significant digits, sci notation at extremes."""
    if x == 0:
        return "0"
    if abs(x) >= 1e15 or abs(x) < 1e-6:
        exp = math.floor(math.log10(abs(x)))
        mant = format(x / 10 ** exp, ".6g")
        return f"{mant} × 10<sup>{exp}</sup>"
    s = format(round(x, 12), ",.10g")
    return s.replace("-", "−")


def label(u, value):
    return u[1] if value == 1 else u[2]


# ---------------------------------------------------------------- templates

e = html.escape


def ad(name, size, label_text, extra_class="", mobile=None):
    w, h = size.split("x")
    sizes = f'<span class="ad-ph-wide">{e(label_text)}, {w} × {h}</span>'
    if mobile:
        mw, mh = mobile.split("x")
        sizes += f'<span class="ad-ph-narrow">{e(label_text)}, {mw} × {mh}</span>'
    # Slot dimensions live in style.css so they can change at mobile breakpoints.
    return (f'<div class="ad ad-{name} {extra_class}" data-ad="{name}" data-size="{size}">'
            f'<span class="ad-label">Advertisement</span>'
            f'<span class="ad-ph">{sizes}</span></div>')


def tiles():
    return ('<section class="ad-tiles" aria-label="Advertisements">'
            + ad("tile-1", "300x250", "Tile 1")
            + ad("tile-2", "300x250", "Tile 2")
            + ad("tile-3", "300x250", "Tile 3", "tile-wide-only")
            + ad("tile-4", "300x250", "Tile 4", "tile-wide-only")
            + '</section>')


LOGO = ('<svg class="logo-mark" viewBox="0 0 32 32" aria-hidden="true">'
        '<rect x="1" y="7" width="30" height="18" rx="2"/>'
        '<path d="M6 7v7M11 7v4M16 7v9M21 7v4M26 7v7"/></svg>')

SWAP_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4 3 8l4 4M3 8h14'
             'M17 20l4-4-4-4M21 16H7"/></svg>')


def nav(prefix, active):
    items = []
    for c in CATEGORIES:
        cur = ' aria-current="page"' if c["slug"] == active else ""
        items.append(f'<li><a href="{prefix}{c["slug"]}/"{cur}>{c["name"]}</a></li>')
    return '<nav class="cats" aria-label="Converters"><ul>' + "".join(items) + "</ul></nav>"


def page(*, path, title, description, body, active=None):
    depth = path.count("/")
    prefix = "../" * depth
    canonical = SITE["url"] + "/" + (path[:-len("index.html")] if path.endswith("index.html") else path)
    year = "2026"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{e(canonical)}">
<meta name="theme-color" content="#F4C430">
<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&display=swap">
<link rel="stylesheet" href="{prefix}assets/css/style.css">
<script src="{prefix}assets/js/ads-config.js"></script>
<script src="{prefix}assets/js/ads.js" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to converter</a>
<header class="site-header">
  <div class="bar">
    <a class="logo" href="{prefix or './'}">{LOGO}<span>{e(SITE["name"])}</span></a>
    <a class="header-link" href="{prefix}about.html">About</a>
  </div>
  {nav(prefix, active)}
</header>
<div class="ad-band ad-band-top">{ad("top-banner", "728x90", "Top banner", mobile="320x100")}</div>
<div class="layout">
  <aside class="rail rail-left" aria-label="Advertisement">{ad("rail-left", "160x600", "Vertical banner")}</aside>
  <main id="main">
{body}
  </main>
  <aside class="rail rail-right" aria-label="Advertisement">{ad("rail-right", "300x600", "Vertical banner")}</aside>
</div>
<div class="ad-band ad-band-bottom">{ad("bottom-banner", "728x90", "Bottom banner", mobile="320x100")}</div>
<footer class="site-footer">
  <div class="footer-inner">
    <p class="footer-name">{e(SITE["name"])}</p>
    <ul class="footer-links">
      <li><a href="{prefix}about.html">About</a></li>
      <li><a href="{prefix}contact.html">Contact</a></li>
      <li><a href="{prefix}privacy.html">Privacy policy</a></li>
    </ul>
    <p class="footer-note">Results are calculated in your browser and rounded to 10 significant digits. &copy; {year} {e(SITE["name"])}</p>
  </div>
</footer>
<aside class="video-ad" id="video-ad" aria-label="Video advertisement" hidden>
  <div class="video-ad-head"><span class="ad-label">Advertisement</span>
    <button type="button" class="icon-btn" data-close-video aria-label="Close video ad">&times;</button></div>
  <div class="video-ad-body" data-ad="video" data-size="320x180"><span class="ad-ph">Video ad, 320 × 180</span></div>
</aside>
<div class="interstitial" id="interstitial" role="dialog" aria-modal="true" aria-label="Advertisement" hidden>
  <div class="interstitial-panel">
    <div class="interstitial-head"><span class="ad-label">Advertisement</span>
      <button type="button" class="continue-btn" data-close-interstitial>Continue to page</button></div>
    <div class="interstitial-body" data-ad="interstitial" data-size="fullscreen"><span class="ad-ph">Full-screen ad</span></div>
  </div>
</div>
{'<script src="' + prefix + 'assets/js/units.js"></script><script src="' + prefix + 'assets/js/converter.js"></script>' if active is not None or path == "index.html" else ""}
</body>
</html>
"""


def converter(cat, *, heading, switchable=False):
    frm, to = cat["default"]
    val = 1
    res = convert(cat, val, frm, to)
    fu, tu = unit(cat, frm), unit(cat, to)
    opts = lambda sel: "".join(
        f'<option value="{u[0]}"{" selected" if u[0] == sel else ""}>{e(u[1][0].upper() + u[1][1:])} ({e(u[3])})</option>'
        for u in cat["units"])
    cat_select = ""
    if switchable:
        cat_opts = "".join(
            f'<option value="{c["slug"]}"{" selected" if c is cat else ""}>{c["name"]}</option>'
            for c in CATEGORIES)
        cat_select = (f'<label class="field field-cat"><span>Measure</span>'
                      f'<select id="cv-category">{cat_opts}</select></label>')
    return f"""<section class="tape" id="converter" data-category="{cat["slug"]}" aria-labelledby="cv-title">
  <div class="tape-ticks" aria-hidden="true"></div>
  <div class="tape-inner">
    <h1 id="cv-title">{e(heading)}</h1>
    <form class="tape-form" onsubmit="return false">
      {cat_select}
      <label class="field field-value"><span>Value</span>
        <input id="cv-value" type="text" inputmode="decimal" autocomplete="off" spellcheck="false" value="1"></label>
      <label class="field field-from"><span>From</span><select id="cv-from">{opts(frm)}</select></label>
      <button type="button" class="swap" id="cv-swap" aria-label="Swap units">{SWAP_ICON}</button>
      <label class="field field-to"><span>To</span><select id="cv-to">{opts(to)}</select></label>
    </form>
    <output class="result" id="cv-result" for="cv-value cv-from cv-to" aria-live="polite">
      <span class="result-num" id="cv-num">{fmt(res)}</span>
      <span class="result-unit" id="cv-unit">{e(label(tu, res))}</span>
    </output>
    <div class="tape-foot">
      <p class="formula" id="cv-formula">1 {e(fu[1])} = {fmt(convert(cat, 1, frm, to))} {e(label(tu, convert(cat, 1, frm, to)))}</p>
      <button type="button" class="copy" id="cv-copy">Copy result</button>
    </div>
  </div>
</section>
<section class="all-units" aria-labelledby="all-title">
  <h2 id="all-title">The same value in every {e(cat["noun"])} unit</h2>
  <table><tbody id="cv-all"></tbody></table>
</section>"""


def reference(cat):
    frm, to = cat["default"]
    fu, tu = unit(cat, frm), unit(cat, to)
    rows = "".join(
        f"<tr><td>{fmt(v)} {e(fu[3])}</td><td>{fmt(convert(cat, v, frm, to))} {e(tu[3])}</td></tr>"
        for v in (1, 2, 5, 10, 20, 50, 100, 500, 1000))
    pairs = "".join(
        f'<li><a href="./?from={a}&amp;to={b}">{e(unit(cat, a)[2].capitalize())} to {e(unit(cat, b)[2])}</a>'
        f'<span>1 {e(unit(cat, a)[3])} = {fmt(convert(cat, 1, a, b))} {e(unit(cat, b)[3])}</span></li>'
        for a, b in cat["popular"])
    return f"""<section class="prose" aria-labelledby="pop-title">
  <h2 id="pop-title">Common {e(cat["noun"])} conversions</h2>
  <ul class="pairs">{pairs}</ul>
</section>
<section class="prose" aria-labelledby="ref-title">
  <h2 id="ref-title">{e(fu[2].capitalize())} to {e(tu[2])} table</h2>
  <table class="ref"><thead><tr><th scope="col">{e(fu[2].capitalize())}</th><th scope="col">{e(tu[2].capitalize())}</th></tr></thead>
  <tbody>{rows}</tbody></table>
</section>"""


def faq(items):
    qs = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in items)
    return f'<section class="prose faq" aria-labelledby="faq-title"><h2 id="faq-title">Questions</h2>{qs}</section>'


def in_content():
    return f'<div class="ad-band ad-band-inline">{ad("in-content", "728x90", "In-content banner", mobile="320x100")}</div>'


def category_page(cat):
    frm, to = cat["default"]
    fu, tu = unit(cat, frm), unit(cat, to)
    body = "\n".join([
        converter(cat, heading=f'{cat["name"]} converter'),
        tiles(),
        f'<section class="prose"><h2>About {e(cat["noun"])} units</h2><p>{e(cat["intro"])}</p></section>',
        in_content(),
        reference(cat),
        faq(cat["faq"]),
    ])
    return page(
        path=f'{cat["slug"]}/index.html',
        title=f'{cat["name"]} converter: {fu[2]} to {tu[2]} and more | {SITE["name"]}',
        description=f'Free {cat["noun"]} converter. {cat["intro"].split(". ")[0]}.',
        body=body, active=cat["slug"])


def home_page():
    cat = BY_SLUG[HOME_DEFAULT]
    rows = []
    for c in CATEGORIES:
        v, a, b = c.get("example", (1,) + tuple(c["default"]))
        ua, ub = unit(c, a), unit(c, b)
        ex = "{} {} = {} {}".format(fmt(v), e(ua[3]), fmt(convert(c, v, a, b)), e(ub[3]))
        names = ", ".join(e(u[2]) for u in c["units"][:4])
        rows.append(f'<li><a href="{c["slug"]}/"><strong>{c["name"]}</strong>'
                    f'<span class="cat-ex">{ex}</span><span class="cat-units">{names} and more</span></a></li>')
    body = "\n".join([
        converter(cat, heading="Unit converter", switchable=True),
        tiles(),
        f'<section class="prose" aria-labelledby="cats-title"><h2 id="cats-title">All converters</h2>'
        f'<ul class="cat-list">{"".join(rows)}</ul></section>',
        in_content(),
        '<section class="prose"><h2>How it works</h2><p>Type a number, pick the unit you have and the '
        'unit you want. The answer updates as you type, and the table under the converter shows the '
        'same value in every other unit of that measure. Conversions use the exact definitions from '
        'the International System of Units and the 1959 international yard and pound agreement, '
        'and run entirely in your browser.</p><p>Each converter has its own page with a reference '
        'table and answers to common questions. You can bookmark or share any conversion: the '
        'address bar keeps the value and units you chose.</p></section>',
        faq([
            ("Are the results exact?",
             "They are calculated from exact definitions and shown to 10 significant digits. Months and years in the time converter are calendar averages."),
            ("Do I need to install anything?",
             "No. The converter works in any modern browser, on phones and desktops."),
            ("Can I share a conversion?",
             "Yes. The page address updates with your value and units, so copy it from the address bar."),
        ]),
    ])
    return page(path="index.html",
                title=f'{SITE["name"]}: length, weight, temperature and more',
                description="Free online unit converter for length, weight, temperature, volume, area, "
                            "speed, time, data, pressure and energy. Results update as you type.",
                body=body, active=None)


def text_page(path, title, description, inner):
    return page(path=path, title=f"{title} | {SITE['name']}", description=description,
                body=f'<article class="prose doc"><h1>{e(title)}</h1>{inner}</article>')


ABOUT = f"""<p>{e(SITE["name"])} is a free, fast converter for everyday and technical units:
length, weight, temperature, volume, area, speed, time, data, pressure and energy.</p>
<p>Every conversion is calculated in your browser from exact definitions. The meter, kilogram
and second come from the International System of Units, and imperial units such as the inch and
pound are defined from them by the 1959 international yard and pound agreement.</p>
<p>The site is supported by advertising, which keeps it free to use. Found a mistake or want
another unit added? <a href="contact.html">Get in touch</a>.</p>"""

CONTACT = f"""<p>Questions, corrections and unit requests are welcome.</p>
<p>Email: <a href="mailto:{e(SITE["email"])}">{e(SITE["email"])}</a></p>
<p>For advertising enquiries, use the same address with "Advertising" in the subject line.</p>"""

PRIVACY = f"""<p>Last updated: October 21, 2026.</p>
<h2>What we collect</h2>
<p>{e(SITE["name"])} does not ask for or store personal information. Values you type into the
converter stay in your browser and are not sent to us.</p>
<h2>Advertising and cookies</h2>
<p>We use Google AdSense and may use other advertising partners to show ads. These third-party
vendors, including Google, use cookies to serve ads based on your previous visits to this
website or other websites.</p>
<p>Google's use of advertising cookies enables it and its partners to serve ads to you based on
your visit to this site and/or other sites on the Internet. You may opt out of personalized
advertising by visiting <a href="https://www.google.com/settings/ads" rel="noopener">Google Ads Settings</a>,
or opt out of some third-party vendors' use of cookies for personalized advertising at
<a href="https://www.aboutads.info/choices/" rel="noopener">www.aboutads.info</a>.</p>
<p>See <a href="https://policies.google.com/technologies/partner-sites" rel="noopener">how Google uses
information from sites that use its services</a>.</p>
<h2>Browser storage</h2>
<p>The site stores a small counter in your browser's session storage so that full-screen ads are
shown at most once per visit. It is deleted when you close the tab.</p>
<h2>Hosting</h2>
<p>The site is served by Cloudflare, which processes standard request data such as IP addresses
to deliver and protect the site.</p>
<h2>Contact</h2>
<p>Questions about this policy: <a href="mailto:{e(SITE["email"])}">{e(SITE["email"])}</a>.</p>"""


def build():
    out = {}
    out["index.html"] = home_page()
    for c in CATEGORIES:
        out[f'{c["slug"]}/index.html'] = category_page(c)
    out["about.html"] = text_page("about.html", "About", f'About {SITE["name"]}.', ABOUT)
    out["contact.html"] = text_page("contact.html", "Contact", f'Contact {SITE["name"]}.', CONTACT)
    out["privacy.html"] = text_page("privacy.html", "Privacy policy",
                                    f'How {SITE["name"]} handles data, cookies and advertising.', PRIVACY)
    out["404.html"] = text_page("404.html", "Page not found", "This page does not exist.",
                                '<p>That address does not match any converter. '
                                '<a href="/">Go to the unit converter</a> or pick a measure above.</p>')

    data = {c["slug"]: {"name": c["name"], "noun": c["noun"], "default": c["default"],
                        "units": [{"id": u[0], "one": u[1], "many": u[2], "sym": u[3], "f": u[4]}
                                  for u in c["units"]]}
            for c in CATEGORIES}
    out["assets/js/units.js"] = ("// Generated by tools/build.py. Do not edit by hand.\n"
                                 "window.UNIT_DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")

    urls = [""] + [c["slug"] + "/" for c in CATEGORIES] + ["about.html", "contact.html", "privacy.html"]
    out["sitemap.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                          + "".join(f"  <url><loc>{SITE['url']}/{u}</loc></url>\n" for u in urls)
                          + "</urlset>\n")

    for rel, text in out.items():
        p = PUBLIC / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(f"Wrote {len(out)} files to {PUBLIC.relative_to(ROOT)}/")


if __name__ == "__main__":
    build()
