// Ad settings. This is the only file you need to edit to turn on ads.
window.AD_CONFIG = {
  // Your AdSense publisher ID, e.g. "ca-pub-1234567890123456". Leave empty until AdSense approves the site.
  // Once set, the AdSense script loads on every page, so Auto ads (including full-screen
  // "vignette" ads and "anchor" ads) can also be switched on from the AdSense dashboard.
  adsenseClient: "",

  // AdSense ad unit IDs (the data-ad-slot number from AdSense > Ads > By ad unit).
  // Create one display ad unit per placement and paste its ID here.
  slots: {
    "top-banner": "",
    "rail-left": "",
    "rail-right": "",
    "tile-1": "",
    "tile-2": "",
    "tile-3": "",
    "tile-4": "",
    "in-content": "",
    "bottom-banner": ""
  },

  // Show grey boxes where ads will go, so you can see the layout.
  // Set to false before going live: unfilled slots then collapse instead of leaving gaps.
  showPlaceholders: true,

  // Floating video ad, bottom right. AdSense does not serve ads into custom floating
  // players, so use a direct-sold video or a video ad network's tag here.
  video: {
    enabled: true,
    delaySeconds: 4,
    // Option A: your own MP4/WebM file plus the advertiser's link.
    src: "",
    link: "",
    // Option B: paste the HTML/script tag a video ad network gives you.
    html: ""
  },

  // Full-screen ad shown when a visitor moves to another page, at most once per visit.
  // For AdSense, use Auto ads > Vignette ads in the dashboard instead; this slot is for
  // direct-sold ads or another network's interstitial tag.
  interstitial: {
    enabled: true,
    // Show on this click to another page on the site (2 = the second page change).
    onNavigation: 2,
    // Option A: an image plus the advertiser's link.
    image: "",
    link: "",
    // Option B: paste an ad network's HTML/script tag.
    html: ""
  }
};
