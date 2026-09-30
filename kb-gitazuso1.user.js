// ==UserScript==
// @name         KB부동산 매물 "기타주소1" 우측상단 표시
// @namespace    dmc.starhub.kbland
// @version      1.1.4
// @description  KB부동산(kbland.kr)에서 매물을 클릭할 때 호출되는 bascInfo API 응답을 가로채, "기타주소1" 값을 화면 우측 상단 오버레이에 표시합니다. 클릭하면 값이 복사됩니다.
// @author       신소장
// @match        https://www.kbland.kr/*
// @match        https://kbland.kr/*
// @match        https://*.kbland.kr/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==

(function () {
  'use strict';

  // ---------------------------------------------------------------------
  // 설정
  // ---------------------------------------------------------------------
  const TARGET_URL_FRAGMENT = '/land-property/property/bascInfo';
  const TARGET_KEY = '기타주소1';
  // 콘솔에 진단 로그를 남길지 여부 (문제가 생기면 true로 바꿔서 다시 진단하세요)
  const DEBUG = false;

  function log(...args) {
    if (DEBUG) console.log('[KB 기타주소1]', ...args);
  }
  function warn(...args) {
    console.warn('[KB 기타주소1]', ...args);
  }

  log('스크립트 로드됨 v1.1.4 — 이 로그가 안 보이면 Tampermonkey가 이 페이지에 스크립트를 실행하지 않은 것입니다.');

  // 좌측 매물 리스트 바로 옆(맵 영역 맨 왼쪽 위)에 붙도록 기본 위치를 잡습니다.
  // 헤더 부분을 드래그하면 원하는 위치로 옮길 수 있고, 옮긴 위치는 기억됩니다.
  const DEFAULT_POS = { top: 12, left: 400 };
  const POS_STORAGE_KEY = 'kbGitazuso1_overlay_pos_v1';

  function loadPos() {
    try {
      const raw = localStorage.getItem(POS_STORAGE_KEY);
      if (!raw) return { ...DEFAULT_POS };
      const parsed = JSON.parse(raw);
      if (typeof parsed.top === 'number' && typeof parsed.left === 'number') {
        return parsed;
      }
    } catch (e) {
      /* 무시 */
    }
    return { ...DEFAULT_POS };
  }

  function savePos(pos) {
    try {
      localStorage.setItem(POS_STORAGE_KEY, JSON.stringify(pos));
    } catch (e) {
      /* 무시 */
    }
  }

  function clampPos(pos) {
    const margin = 8;
    const maxLeft = Math.max(margin, window.innerWidth - 240);
    const maxTop = Math.max(margin, window.innerHeight - 60);
    return {
      top: Math.min(Math.max(pos.top, margin), maxTop),
      left: Math.min(Math.max(pos.left, margin), maxLeft)
    };
  }

  // 이 스크립트에서 발생한 예외인지 판별하는 패턴 (진단용)
  const OWN_ERROR_PATTERN = /kbGitazuso1|handleResponseData|findKeyDeep|showValue|showNotFound|ensureOverlay|extractMatId|copyToClipboard/;

  window.addEventListener('error', function (e) {
    try {
      const stack = e && e.error && e.error.stack;
      if (stack && OWN_ERROR_PATTERN.test(stack)) {
        console.error('[KB 기타주소1] ⚠️ 스크립트 내부 예외 발생:', e.error);
      }
    } catch (_) {
      /* 무시 */
    }
  });

  window.addEventListener('unhandledrejection', function (e) {
    try {
      const stack = e && e.reason && e.reason.stack;
      if (stack && OWN_ERROR_PATTERN.test(stack)) {
        console.error('[KB 기타주소1] ⚠️ 처리되지 않은 Promise 거부:', e.reason);
      }
    } catch (_) {
      /* 무시 */
    }
  });

  // ---------------------------------------------------------------------
  // 오버레이 UI
  // ---------------------------------------------------------------------
  let overlayEl = null;
  let valueEl = null;
  let subEl = null;
  let statusEl = null;

  function ensureOverlay() {
    if (overlayEl && document.body && document.body.contains(overlayEl)) {
      return overlayEl;
    }

    const pos = clampPos(loadPos());

    overlayEl = document.createElement('div');
    overlayEl.id = 'kb-gitazuso1-overlay';
    overlayEl.style.cssText = [
      'position:fixed',
      `top:${pos.top}px`,
      `left:${pos.left}px`,
      'z-index:2147483647',
      'min-width:220px',
      'max-width:320px',
      'background:#ffffff',
      'border:1px solid #dfe3e8',
      'border-radius:10px',
      'box-shadow:0 6px 18px rgba(0,0,0,0.15)',
      'padding:0 12px 10px',
      'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Malgun Gothic",sans-serif',
      'font-size:13px',
      'color:#222',
      'line-height:1.4',
      'user-select:text',
      'transition:box-shadow .15s ease'
    ].join(';');

    overlayEl.addEventListener('mouseenter', () => {
      overlayEl.style.boxShadow = '0 8px 22px rgba(0,0,0,0.22)';
    });
    overlayEl.addEventListener('mouseleave', () => {
      overlayEl.style.boxShadow = '0 6px 18px rgba(0,0,0,0.15)';
    });

    // 헤더 = 드래그 손잡이 (여기를 눌러서 끌면 위치를 옮길 수 있고, 옮긴 위치는 기억됩니다)
    const header = document.createElement('div');
    header.style.cssText = 'display:flex;align-items:center;justify-content:space-between;margin:0 -12px 4px;padding:8px 12px;cursor:move;border-bottom:1px solid #f0f1f3;';

    const label = document.createElement('div');
    label.textContent = '기타주소1  ⠿';
    label.title = '드래그해서 위치를 옮길 수 있습니다';
    label.style.cssText = 'font-size:11px;color:#888;font-weight:600;letter-spacing:.2px;';

    const closeBtn = document.createElement('div');
    closeBtn.textContent = '×';
    closeBtn.title = '숨기기';
    closeBtn.style.cssText = 'font-size:16px;color:#aaa;line-height:14px;padding:0 2px;cursor:pointer;';
    closeBtn.addEventListener('mousedown', (e) => e.stopPropagation());
    closeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      overlayEl.style.display = 'none';
    });

    header.appendChild(label);
    header.appendChild(closeBtn);

    // 본문 = 클릭하면 값이 복사됩니다
    const body = document.createElement('div');
    body.style.cssText = 'cursor:pointer;padding-top:6px;';

    valueEl = document.createElement('div');
    valueEl.textContent = '매물을 클릭하면 여기에 표시됩니다';
    valueEl.style.cssText = 'font-size:15px;font-weight:700;color:#111;word-break:break-all;';

    subEl = document.createElement('div');
    subEl.style.cssText = 'font-size:11px;color:#999;margin-top:4px;';

    statusEl = document.createElement('div');
    statusEl.style.cssText = 'font-size:11px;color:#2f8f4e;margin-top:4px;height:14px;';

    body.appendChild(valueEl);
    body.appendChild(subEl);
    body.appendChild(statusEl);

    overlayEl.appendChild(header);
    overlayEl.appendChild(body);

    body.addEventListener('click', () => {
      const text = valueEl.dataset.rawValue || '';
      if (!text) return;
      copyToClipboard(text);
    });

    // ---- 드래그 처리 ----
    let dragging = false;
    let dragStartX = 0;
    let dragStartY = 0;
    let boxStartLeft = 0;
    let boxStartTop = 0;

    header.addEventListener('mousedown', (e) => {
      dragging = true;
      dragStartX = e.clientX;
      dragStartY = e.clientY;
      const rect = overlayEl.getBoundingClientRect();
      boxStartLeft = rect.left;
      boxStartTop = rect.top;
      e.preventDefault();
    });

    window.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      const newLeft = boxStartLeft + (e.clientX - dragStartX);
      const newTop = boxStartTop + (e.clientY - dragStartY);
      overlayEl.style.left = `${newLeft}px`;
      overlayEl.style.top = `${newTop}px`;
      overlayEl.style.right = 'auto';
    });

    window.addEventListener('mouseup', () => {
      if (!dragging) return;
      dragging = false;
      const rect = overlayEl.getBoundingClientRect();
      savePos({ top: Math.round(rect.top), left: Math.round(rect.left) });
      log('오버레이 위치 저장:', Math.round(rect.left), Math.round(rect.top));
    });

    const attach = () => {
      if (document.body) {
        document.body.appendChild(overlayEl);
        log('오버레이 박스를 화면에 부착했습니다.');
      } else {
        document.addEventListener('DOMContentLoaded', attach, { once: true });
      }
    };
    attach();

    return overlayEl;
  }

  function copyToClipboard(text) {
    const done = () => {
      if (statusEl) {
        statusEl.textContent = '복사됨!';
        setTimeout(() => {
          if (statusEl) statusEl.textContent = '';
        }, 1200);
      }
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(() => fallbackCopy(text, done));
    } else {
      fallbackCopy(text, done);
    }
  }

  function fallbackCopy(text, done) {
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      done();
    } catch (e) {
      /* 무시 */
    }
  }

  function showValue(value, matchId) {
    ensureOverlay();
    overlayEl.style.display = 'block';
    if (value === null || value === undefined || value === '') {
      valueEl.textContent = '(값 없음)';
      valueEl.dataset.rawValue = '';
    } else {
      valueEl.textContent = String(value);
      valueEl.dataset.rawValue = String(value);
    }
    subEl.textContent = matchId ? `매물일련번호: ${matchId}` : '';
    statusEl.textContent = '';
  }

  function showNotFound(matchId) {
    ensureOverlay();
    overlayEl.style.display = 'block';
    valueEl.textContent = '기타주소1 항목을 찾지 못했습니다 (콘솔 확인)';
    valueEl.dataset.rawValue = '';
    subEl.textContent = matchId ? `매물일련번호: ${matchId}` : '';
    statusEl.textContent = '';
  }

  // ---------------------------------------------------------------------
  // 응답 데이터에서 재귀적으로 TARGET_KEY 찾기
  // ---------------------------------------------------------------------
  function findKeyDeep(obj, key, path = '') {
    if (obj === null || typeof obj !== 'object') return null;

    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      return { value: obj[key], path: path ? `${path}.${key}` : key };
    }

    if (Array.isArray(obj)) {
      for (let i = 0; i < obj.length; i++) {
        const found = findKeyDeep(obj[i], key, `${path}[${i}]`);
        if (found) return found;
      }
      return null;
    }

    for (const k of Object.keys(obj)) {
      const found = findKeyDeep(obj[k], key, path ? `${path}.${k}` : k);
      if (found) return found;
    }
    return null;
  }

  function extractMatId(url) {
    try {
      const u = new URL(url, location.href);
      const raw = u.searchParams.get('매물일련번호');
      if (raw) return raw;
      for (const [k, v] of u.searchParams.entries()) {
        if (decodeURIComponent(k) === '매물일련번호') return v;
      }
    } catch (e) {
      /* 무시 */
    }
    return null;
  }

  // data는 문자열(JSON 텍스트)일 수도, 이미 파싱된 객체일 수도 있습니다.
  // (axios 등은 XHR responseType을 'json'으로 설정해 브라우저가 자동 파싱하는 경우가 많습니다.)
  function handleResponseData(url, data) {
    let json;

    if (data && typeof data === 'object') {
      json = data;
    } else if (typeof data === 'string') {
      try {
        json = JSON.parse(data);
      } catch (e) {
        warn('응답이 JSON 텍스트가 아닙니다:', url, data && data.slice ? data.slice(0, 200) : data);
        return;
      }
    } else {
      warn('처리할 수 없는 응답 형식입니다 (Blob/ArrayBuffer 등):', url, typeof data);
      return;
    }

    const matId = extractMatId(url);
    const found = findKeyDeep(json, TARGET_KEY);

    if (found) {
      log(`발견 (경로: ${found.path}):`, found.value);
      showValue(found.value, matId);
    } else {
      warn('키를 찾지 못했습니다. 전체 응답:', json);
      showNotFound(matId);
    }
  }

  // ---------------------------------------------------------------------
  // fetch 가로채기
  // ---------------------------------------------------------------------
  const originalFetch = window.fetch;
  if (typeof originalFetch === 'function') {
    window.fetch = function (input, init) {
      const url = typeof input === 'string' ? input : (input && input.url) || '';
      const promise = originalFetch.apply(this, arguments);
      if (url && url.indexOf(TARGET_URL_FRAGMENT) !== -1) {
        log('fetch 요청 감지:', url);
        promise
          .then((res) => {
            res
              .clone()
              .text()
              .then((text) => handleResponseData(url, text))
              .catch((e) => warn('fetch 응답 읽기 실패:', e));
            return res;
          })
          .catch((e) => warn('fetch 실패:', e));
      }
      return promise;
    };
  }

  // ---------------------------------------------------------------------
  // XMLHttpRequest 가로채기 (axios 등 대부분의 KB부동산 API 호출이 이 방식입니다)
  // ---------------------------------------------------------------------
  const OrigXHR = window.XMLHttpRequest;
  if (OrigXHR) {
    const origOpen = OrigXHR.prototype.open;
    const origSend = OrigXHR.prototype.send;

    OrigXHR.prototype.open = function (method, url) {
      this.__kbGitazuso1Url = url;
      this.__kbGitazuso1Match = typeof url === 'string' && url.indexOf(TARGET_URL_FRAGMENT) !== -1;
      return origOpen.apply(this, arguments);
    };

    OrigXHR.prototype.send = function () {
      if (this.__kbGitazuso1Match) {
        const url = this.__kbGitazuso1Url;
        log('XHR 요청 감지:', url, '(responseType=' + (this.responseType || '(빈값/text)') + ')');
        this.addEventListener('load', function () {
          try {
            // responseType이 'json'이면 responseText 접근 시 예외가 발생하므로 response를 우선 사용
            const data = this.responseType && this.responseType !== '' && this.responseType !== 'text'
              ? this.response
              : this.responseText;
            handleResponseData(url, data);
          } catch (e) {
            warn('XHR 응답 처리 중 오류:', e);
          }
        });
        this.addEventListener('error', function () {
          warn('XHR 요청 실패:', url);
        });
      }
      return origSend.apply(this, arguments);
    };
  }

  // 페이지 로드 시 오버레이 미리 준비
  ensureOverlay();
})();