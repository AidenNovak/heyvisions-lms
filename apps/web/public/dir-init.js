// Runs synchronously in <head>, before <body> paints, so an RTL locale never
// flashes an LTR layout. Same reason and same mechanism as embed-bg.js.
//
// The server cannot do this: i18next's highest-priority detection source is
// localStorage, which is client-only. So the detection order below MIRRORS
// `detection.order` in lib/i18n.ts exactly — localStorage, cookie, querystring,
// navigator.
//
// The RTL list is duplicated from RTL_LANGUAGES in lib/direction.ts, because
// this file runs before any bundle loads and cannot import it.
// tests/rtl-guard.test.mjs asserts the two lists stay in sync — update both.
//
// **Yet to Dawn fork**: 未显式选过语言时用平台默认语言（NEXT_PUBLIC_DEFAULT_LANGUAGE，
// 默认 zh），而不是浏览器语言。理由见 lib/i18n.ts 的 initialLanguage()：
// 课程面向中文学习者，用浏览器语言会让英文浏览器的学习者先看到约 4 秒英文界面。
// 两处必须用同一个「用户选过没有」的标记，改一处要改另一处。
// 本文件在 runtime-config.js 之后加载，所以读得到 window.__RUNTIME_CONFIG__。
(function () {
  var RTL = {
    ar: 1, fa: 1, he: 1, iw: 1, ur: 1, ps: 1,
    sd: 1, ug: 1, yi: 1, dv: 1, ckb: 1,
  };

  function userPicked() {
    try {
      return !!localStorage.getItem('i18nextLng_userPicked');
    } catch { return false }
  }

  function detect() {
    try {
      var stored = localStorage.getItem('i18nextLng');
      if (stored) return stored;
    } catch { /* private mode / sandboxed iframe */ }

    var cookie = document.cookie.match(/(?:^|;\s*)i18next=([^;]*)/);
    if (cookie) {
      try { return decodeURIComponent(cookie[1]) } catch { /* malformed */ }
    }

    try {
      var qs = new URLSearchParams(location.search).get('lng');
      if (qs) return qs;
    } catch { /* malformed query string */ }

    return (navigator.languages && navigator.languages[0]) || navigator.language || 'en';
  }

  // 用户显式选过语言就尊重它；否则用平台默认语言。
  var code;
  if (userPicked()) {
    code = String(detect() || 'en').split('-')[0].toLowerCase();
  } else {
    var cfg = window.__RUNTIME_CONFIG__ || {};
    code = String(cfg.NEXT_PUBLIC_DEFAULT_LANGUAGE || 'zh').split('-')[0].toLowerCase();
  }
  var dir = RTL[code] ? 'rtl' : 'ltr';

  var el = document.documentElement;
  el.setAttribute('lang', code);
  el.setAttribute('dir', dir);
  el.style.setProperty('--dir', dir === 'rtl' ? '-1' : '1');
})();
