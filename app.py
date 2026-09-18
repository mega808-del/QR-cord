# -*- coding: utf-8 -*-
"""
연락처 QR코드 생성기 (웹 버전)
- 이름 + 휴대폰 번호만 입력하면 갤럭시/아이폰 공용 vCard QR코드 생성
- 다운로드 및 공유 링크 제공: 받은 사람이 링크를 열면 모바일에서 원터치 저장 가능
실행: python app.py  →  http://127.0.0.1:5000 접속
"""
import base64
import html
import io
import json
import os
import re
import secrets
import socket
import sys
from datetime import datetime

from flask import Flask, request, jsonify, send_file, Response, abort
import qrcode
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")

app = Flask(__name__)

os.makedirs("saved_qrcodes", exist_ok=True)  # QR 백업 저장 폴더 보장

# 공유 링크용 QR 저장소 (메모리 기반, 서버 재시작 시 초기화)
QR_STORE: dict[str, dict] = {}
MAX_STORE = 100  # 최대 보관 개수(초과 시 가장 오래된 것부터 삭제)


def get_lan_ip() -> str:
    """스마트폰이 같은 Wi-Fi에서 접속할 수 있는 PC의 내부 IP 확인."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
__PWA_HEAD__
<title>연락처 QR코드 생성기</title>
<style>
  :root {
    --bg: #f4f6fb; --card: #ffffff; --text: #1c2333; --sub: #66708a;
    --accent: #3b6cf6; --accent-press: #2f55c9; --border: #dfe4f0;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #12151d; --card: #1c212e; --text: #eef1f8; --sub: #9aa3bd;
      --border: #2c3346;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px 16px; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Malgun Gothic",
                 "Apple SD Gothic Neo", sans-serif;
    display: flex; justify-content: center;
  }
  .wrap { width: 100%; max-width: 430px; }
  h1 { font-size: 22px; margin: 8px 0 4px; }
  .desc { color: var(--sub); font-size: 14px; margin: 0 0 20px; }
  .card {
    background: var(--card); border: 1px solid var(--border); border-radius: 14px;
    padding: 20px; box-shadow: 0 4px 14px rgba(20, 30, 60, .06);
  }
  label { display: block; font-size: 13px; font-weight: 600; margin: 14px 0 6px; }
  label:first-child { margin-top: 0; }
  input {
    width: 100%; padding: 12px 14px; font-size: 16px; color: var(--text);
    background: var(--bg); border: 1px solid var(--border); border-radius: 10px;
    outline: none;
  }
  input:focus { border-color: var(--accent); }
  button {
    width: 100%; margin-top: 18px; padding: 14px; font-size: 16px; font-weight: 700;
    color: #fff; background: var(--accent); border: none; border-radius: 10px;
    cursor: pointer;
  }
  button:active { background: var(--accent-press); }
  button:disabled { opacity: .55; cursor: wait; }
  #result { display: none; margin-top: 20px; text-align: center; }
  #qrimg {
    width: 240px; height: 240px; border-radius: 12px;
    border: 1px solid var(--border); background: #fff;
  }
  .who { font-size: 16px; font-weight: 700; margin: 12px 0 2px; }
  .tel { color: var(--sub); font-size: 14px; margin: 0 0 14px; }
  .btnrow { display: flex; gap: 10px; }
  .btnrow button { margin-top: 0; }
  .btnrow2 { display: flex; gap: 10px; margin-top: 10px; }
  .ghost {
    background: transparent; color: var(--accent);
    border: 1.5px solid var(--accent);
  }
  .install {
    color: var(--accent); background: var(--bg);
    border: 1.5px dashed var(--accent); font-size: 15px; padding: 13px;
  }
  .overlay {
    position: fixed; inset: 0; background: rgba(15, 20, 34, .55);
    display: none; align-items: center; justify-content: center; padding: 20px;
    z-index: 1000;
  }
  .overlay.open { display: flex; }
  .modal {
    background: var(--card); color: var(--text); width: 100%; max-width: 360px;
    border-radius: 16px; padding: 22px 20px; text-align: left;
    box-shadow: 0 12px 40px rgba(10, 16, 34, .35);
  }
  .modal h3 { margin: 0 0 8px; font-size: 17px; text-align: center; }
  .modal ol { margin: 10px 0 0; padding-left: 20px; font-size: 13.5px; line-height: 1.7; }
  .modal .close {
    margin-top: 16px; width: 100%; padding: 12px; border: none; border-radius: 10px;
    background: var(--accent); color: #fff; font-size: 15px; font-weight: 700; cursor: pointer;
  }
  .appicon {
    width: 56px; height: 56px; border-radius: 14px; display: block; margin: 0 auto 8px;
    box-shadow: 0 3px 10px rgba(20, 30, 60, .25);
  }
  #sharelink {
    display: none; margin-top: 12px; font-size: 12.5px; color: var(--sub);
    word-break: break-all; cursor: pointer;
    text-decoration: underline; text-underline-offset: 3px;
  }
  #status {
    margin-top: 14px; font-size: 14px; min-height: 20px; color: var(--sub);
    word-break: keep-all;
  }
  .error { color: #e5484d !important; font-weight: 600; }
  .ok { color: #2fa96e !important; font-weight: 600; }
</style>
</head>
<body>
<div class="wrap">
  <h1>📇 연락처 QR코드 생성기</h1>
  <p class="desc">이름과 휴대폰 번호만 입력하세요. 스캔하면 연락처로 저장되는 QR코드를 만들어 드립니다. (갤럭시/아이폰 공용)</p>

  <div class="card">
    <form id="qrform">
      <label for="name">이름</label>
      <input id="name" name="name" placeholder="예: 홍길동" maxlength="30" required autocomplete="name">

      <label for="phone">휴대폰 번호</label>
      <input id="phone" name="phone" placeholder="예: 010-2345-6789" maxlength="20" required inputmode="tel" autocomplete="tel">

      <button type="submit" id="genBtn">QR코드 생성</button>
    </form>

    <div id="result">
      <img id="qrimg" alt="연락처 QR코드">
      <div class="who" id="who"></div>
      <div class="tel" id="tel"></div>
      <div class="btnrow">
        <button type="button" id="installBtn">📱 앱으로 설치</button>
        <button type="button" id="shareBtn" class="ghost">🔗 공유</button>
      </div>
      <div class="btnrow2">
        <button type="button" id="downloadBtn" class="ghost">⬇️ 이미지 저장</button>
        <button type="button" id="backBtn" class="ghost">↺ 새로 만들기</button>
      </div>
      <div id="sharelink" title="클릭하면 링크가 복사됩니다"></div>
    </div>

    <div id="status"></div>
  </div>

  <div class="overlay" id="installOverlay">
    <div class="modal" role="dialog" aria-modal="true">
      <img class="appicon" src="/icon-192.png" alt="연락처QR 앱 아이콘">
      <h3>📱 연락처QR 앱으로 설치</h3>
      <ol id="stepGeneric">
        <li>브라우저 메뉴(⋮ 또는 ☰)를 여세요.</li>
        <li><b>[앱 설치]</b> 또는 <b>[홈 화면에 추가]</b>를 선택하세요.</li>
        <li>설치하면 바탕화면에 <b>"연락처QR"</b> 아이콘이 생깁니다.</li>
      </ol>
      <div id="stepIos" style="display:none">
        <ol>
          <li>하단의 <b>공유 버튼</b>(□에 ↑)을 누르세요.</li>
          <li><b>[홈 화면에 추가]</b>를 선택하세요.</li>
          <li>우측 상단 <b>[추가]</b>를 누르면 바탕화면에 설치됩니다.</li>
        </ol>
      </div>
      <button type="button" class="close" id="installClose">닫기</button>
    </div>
  </div>
</div>

<script>
var form = document.getElementById('qrform');
var genBtn = document.getElementById('genBtn');
var result = document.getElementById('result');
var qrimg = document.getElementById('qrimg');
var who = document.getElementById('who');
var tel = document.getElementById('tel');
var statusEl = document.getElementById('status');
var downloadBtn = document.getElementById('downloadBtn');
var shareBtn = document.getElementById('shareBtn');
var sharelinkEl = document.getElementById('sharelink');
var installBtn = document.getElementById('installBtn');
var backBtn = document.getElementById('backBtn');
var installOverlay = document.getElementById('installOverlay');
var installClose = document.getElementById('installClose');
var deferredPrompt = null;

// 네이티브 설치 프롬프트 지원 브라우저(HTTPS/localhost의 Chrome 등)는 이벤트 저장 후 사용
var waitingForPrompt = null;   // 클릭 후 프롬프트 도착을 기다리는 중이면 호출됨
window.addEventListener('beforeinstallprompt', function (e) {
  e.preventDefault();
  deferredPrompt = e;
  if (waitingForPrompt) { waitingForPrompt(); waitingForPrompt = null; }
});
window.addEventListener('appinstalled', function () {
  deferredPrompt = null;
  setStatus('✅ 설치 완료! 바탕화면에서 "연락처QR" 앱을 사용할 수 있어요.', 'ok');
});

var currentBlob = null;
var currentName = '';
var currentPhone = '';
var qrId = null;
var LAN_ORIGIN = '__LAN__';  // 서버가 주입 (PC의 내부 IP:포트)

function setStatus(msg, cls) {
  statusEl.textContent = msg || '';
  statusEl.className = cls || '';
}

function safeFile(name) {
  return 'vcard_' + (name || 'contact').replace(/[\\\\/:*?"<>|\\s]+/g, '') + '.png';
}

function shareBaseUrl() {
  var h = location.hostname;
  if (h === '127.0.0.1' || h === 'localhost') {
    return location.protocol + '//' + LAN_ORIGIN;  // 스마트폰 접속용 주소
  }
  return location.origin;
}

function copyText(t) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(t);
  }
  return new Promise(function (resolve, reject) {
    var ta = document.createElement('textarea');
    ta.value = t;
    ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus(); ta.select();
    try {
      var ok = document.execCommand('copy');
      ok ? resolve() : reject(new Error('copy failed'));
    } catch (e) { reject(e); }
    finally { ta.remove(); }
  });
}

form.addEventListener('submit', async function (e) {
  e.preventDefault();
  var name = document.getElementById('name').value.trim();
  var phone = document.getElementById('phone').value.trim();
  if (!name || !phone) { setStatus('이름과 휴대폰 번호를 모두 입력해 주세요.', 'error'); return; }

  genBtn.disabled = true;
  setStatus('QR코드를 생성하는 중...', '');
  try {
    var res = await fetch('/api/qr', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name, phone: phone })
    });
    if (!res.ok) {
      var msg = '생성 실패 (서버 오류)';
      try { var j = await res.json(); if (j.error) msg = j.error; } catch (_) {}
      throw new Error(msg);
    }
    currentBlob = await res.blob();
    if (qrimg.src.startsWith('blob:')) URL.revokeObjectURL(qrimg.src);
    qrimg.src = URL.createObjectURL(currentBlob);
    currentName = name;
    currentPhone = phone;
    qrId = res.headers.get('X-Qr-Id');
    who.textContent = name;
    tel.textContent = phone;
    if (qrId) {
      var link = shareBaseUrl() + '/s/' + qrId;
      sharelinkEl.textContent = '공유 링크: ' + link;
      sharelinkEl.style.display = 'block';
    } else {
      sharelinkEl.style.display = 'none';
    }
    result.style.display = 'block';
    form.style.display = 'none';          // 입력폼 숨김 → QR/설치/공유에 집중
    setStatus('생성 완료! 설치하거나 공유할 수 있어요.', 'ok');
  } catch (err) {
    setStatus(err.message || '오류가 발생했습니다.', 'error');
  } finally {
    genBtn.disabled = false;
  }
});

// "새로 만들기" → 입력폼으로 복귀 (입력값 유지)
backBtn.addEventListener('click', function () {
  result.style.display = 'none';
  form.style.display = '';
  setStatus('이름과 번호를 입력하세요.', '');
});

// ---- 설치된 앱/바로가기로 열 때: 마지막 생성 QR 즉시 표시 ----
function showRestoredQR(d) {
  currentBlob = null;                       // blob 없음 → 다운로드는 /qr/<id> 경유
  currentName = d.name;
  currentPhone = d.phone;
  qrId = d.qid;
  qrimg.src = 'data:image/png;base64,' + d.png_b64;
  who.textContent = d.name;
  tel.textContent = d.phone;
  var link = shareBaseUrl() + '/s/' + d.qid;
  sharelinkEl.textContent = '공유 링크: ' + link;
  sharelinkEl.style.display = 'block';
  result.style.display = 'block';
  form.style.display = 'none';
  setStatus('마지막으로 생성한 QR입니다. [새로 만들기]로 다른 QR을 만들 수 있어요.', '');
}

(async function restoreLastQR() {
  try {
    var res = await fetch('/api/last-qr');
    var d = await res.json();
    if (d && d.exists) showRestoredQR(d);
  } catch (_) { /* 조용히 입력폼 유지 */ }
})();

// ---- 앱 설치(PWA): 클릭 한 번으로 바탕화면 설치 ----
function isStandalone() {
  return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
}

// 클릭 시 설치 팝업이 아직 안 왔으면 잠시 기다렸다가 띄움 (원터치 설치)
function waitForPrompt(ms) {
  return new Promise(function (resolve) {
    if (deferredPrompt) { resolve(true); return; }
    var done = false;
    waitingForPrompt = function () { if (!done) { done = true; resolve(true); } };
    setTimeout(function () {
      if (!done) { done = true; waitingForPrompt = null; resolve(false); }
    }, ms);
  });
}

function showInstallGuide() {
  // iOS(사파리)는 네이티브 설치 프롬프트가 없어 공유 메뉴 경로 안내
  var isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) ||
              (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  document.getElementById('stepGeneric').style.display = isIOS ? 'none' : '';
  document.getElementById('stepIos').style.display = isIOS ? '' : 'none';
  installOverlay.classList.add('open');
}

installBtn.addEventListener('click', async function () {
  if (isStandalone()) { setStatus('이미 앱(설치 모드)으로 실행 중입니다.'); return; }
  setStatus('설치 팝업을 준비하는 중...', '');
  var has = await waitForPrompt(2500);   // 설치 팝업 대기 (최대 2.5초)
  if (has && deferredPrompt) {           // 1) 네이티브 설치 팝업 표시 → 확인 한 번으로 설치
    try {
      deferredPrompt.prompt();
      var choice = await deferredPrompt.userChoice;
      if (choice && choice.outcome === 'accepted') return;  // 완료는 appinstalled에서 안내
      deferredPrompt = null;
      setStatus('설치가 취소되었습니다. 버튼을 다시 누르면 설치할 수 있어요.', '');
    } catch (_) { deferredPrompt = null; }
    return;
  }
  showInstallGuide();                    // 2) 미지원 환경: 브라우저별 수동 설치 안내
});

installClose.addEventListener('click', function () {
  installOverlay.classList.remove('open');
});

installOverlay.addEventListener('click', function (e) {
  if (e.target === installOverlay) installOverlay.classList.remove('open');
});

downloadBtn.addEventListener('click', async function () {
  // 복원 상태(blob 없음)에서는 서버에서 받아와 저장
  if (!currentBlob && qrId) {
    try {
      var res = await fetch('/qr/' + qrId);
      currentBlob = await res.blob();
    } catch (_) { setStatus('이미지를 가져오지 못했습니다.', 'error'); return; }
  }
  if (!currentBlob) return;
  var a = document.createElement('a');
  a.href = URL.createObjectURL(currentBlob);
  a.download = safeFile(currentName);
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(function () { URL.revokeObjectURL(a.href); }, 3000);
  setStatus('이미지를 다운로드했습니다.', 'ok');
});

async function shareCurrent() {
  if (!currentBlob) return;
  var file = new File([currentBlob], safeFile(currentName), { type: 'image/png' });
  // 1) 모바일/데스크톱 공유 시트 지원 시
  if (navigator.canShare && navigator.canShare({ files: [file] })) {
    try {
      await navigator.share({ files: [file], title: currentName + ' 연락처 QR코드' });
      setStatus('공유했습니다.', 'ok');
    } catch (err) {
      if (err && err.name !== 'AbortError') setStatus('공유가 취소되었습니다.', '');
    }
    return;
  }
  // 2) 공유 링크 복사 (받은 사람이 열면 바로 저장 가능)
  if (qrId) {
    var link = shareBaseUrl() + '/s/' + qrId;
    try {
      await copyText(link);
      setStatus('공유 링크를 복사했습니다! 메신저로 보내면 상대방이 바로 저장할 수 있어요.', 'ok');
    } catch (err) {
      setStatus('공유 링크: ' + link, '');
    }
    return;
  }
  // 3) 클립보드 이미지 복사 폴백
  try {
    await navigator.clipboard.write([new ClipboardItem({ 'image/png': currentBlob })]);
    setStatus('이미지를 클립보드에 복사했습니다.', 'ok');
  } catch (err) {
    setStatus('이 브라우저는 공유를 지원하지 않습니다. 다운로드 버튼을 이용해 주세요.', 'error');
  }
}

shareBtn.addEventListener('click', shareCurrent);
sharelinkEl.addEventListener('click', function () {
  var link = shareBaseUrl() + '/s/' + qrId;
  copyText(link).then(function () {
    setStatus('공유 링크를 복사했습니다!', 'ok');
  }).catch(function () {});
});
</script>
__SW__
</body>
</html>"""


# ---------------------------------------------------------------
# PWA (모바일 앱 설치) 지원 — 아이콘 동적 생성, 매니페스트, 서비스 워커
# ---------------------------------------------------------------
PWA_HEAD = (
    '<meta name="theme-color" content="#3b6cf6">\n'
    '<meta name="mobile-web-app-capable" content="yes">\n'
    '<meta name="apple-mobile-web-app-capable" content="yes">\n'
    '<meta name="apple-mobile-web-app-title" content="연락처QR">\n'
    '<meta name="apple-mobile-web-app-status-bar-style" content="default">\n'
    '<link rel="manifest" href="/manifest.webmanifest">\n'
    '<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">\n'
    '<link rel="apple-touch-icon" href="/icon-512.png">'
)

_SW_REGISTER = (
    '<script>'
    "if ('serviceWorker' in navigator) {"
    "window.addEventListener('load', function () {"
    "navigator.serviceWorker.register('/sw.js').catch(function () {});"
    "});}"
    '</script>'
)

_MANIFEST = {
    "name": "연락처QR — 연락처 QR코드 생성기",
    "short_name": "연락처QR",
    "description": "이름과 휴대폰 번호만 입력하면 갤럭시/아이폰 공용 연락처 QR코드를 생성합니다.",
    "lang": "ko",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#f4f6fb",
    "theme_color": "#3b6cf6",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "/icon-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}

_SW_JS = (
    "// 연락처QR 서비스 워커 — 정적 아이콘 캐시 전용 (페이지는 항상 네트워크)\n"
    "var CACHE = 'contact-qr-static-v1';\n"
    "var ASSETS = ['/icon-192.png', '/icon-512.png', '/icon-maskable.png'];\n"
    "self.addEventListener('install', function (e) {\n"
    "  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(ASSETS); })\n"
    "    .then(function () { return self.skipWaiting(); }));\n"
    "});\n"
    "self.addEventListener('activate', function (e) {\n"
    "  e.waitUntil(caches.keys().then(function (keys) {\n"
    "    return Promise.all(keys.filter(function (k) { return k !== CACHE; })\n"
    "      .map(function (k) { return caches.delete(k); }));\n"
    "  }).then(function () { return self.clients.claim(); }));\n"
    "});\n"
    "self.addEventListener('fetch', function (e) {\n"
    "  if (e.request.method !== 'GET') return;\n"
    "  var path = new URL(e.request.url).pathname;\n"
    "  if (ASSETS.indexOf(path) === -1) return;  // 나머지는 전부 네트워크로 통과\n"
    "  e.respondWith(caches.match(e.request).then(function (hit) { return hit || fetch(e.request); }));\n"
    "});\n"
)

_ICON_CACHE: dict[tuple[int, bool], bytes] = {}


def _load_icon_font(px: int):
    """이모지 렌더링용 컬러 폰트 탐색 (플랫폼별 후보 → 기본 폰트 폴백)."""
    for path in (
        "C:/Windows/Fonts/seguiemj.ttf",                      # Windows
        "/System/Library/Fonts/Apple Color Emoji.ttc",        # macOS
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",  # Linux
        "/system/fonts/NotoColorEmoji.ttf",                   # Android(에뮬레이터 등)
    ):
        try:
            return ImageFont.truetype(path, px)
        except Exception:
            continue
    return ImageFont.load_default()


def make_app_icon(size: int = 512, maskable: bool = False) -> bytes:
    """PWA 설치용 앱 아이콘 PNG (파랑 그라디언트 + 📇) 생성 후 캐시."""
    key = (size, maskable)
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)
    top, bot = (76, 125, 255), (39, 73, 201)  # #4c7dff → #2749c9 그라디언트
    for y in range(size):
        t = y / max(1, size - 1)
        draw.line([(0, y), (size, y)],
                  fill=(int(top[0] + (bot[0] - top[0]) * t),
                        int(top[1] + (bot[1] - top[1]) * t),
                        int(top[2] + (bot[2] - top[2]) * t)))

    out = img.convert("RGBA")

    # 이모지를 큰 캔버스에 그린 뒤 실측 크기로 리사이즈(글리프 여백 제거)
    emoji = None
    try:
        tmp = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((size, size), "📇",
                                 font=_load_icon_font(int(size * 1.2)),
                                 embedded_color=True, anchor="mm")
        bbox = tmp.getbbox()
        if bbox:
            emoji = tmp.crop(bbox)
    except Exception:
        emoji = None

    if emoji:
        target = int(size * (0.68 if maskable else 0.76))  # maskable 안전영역 확보
        emoji = emoji.resize((target, target), Image.LANCZOS)
        out.alpha_composite(emoji, ((size - target) // 2, (size - target) // 2))
    else:
        # 이모지 렌더링 실패 환경용 대체 그래픽: 흰 카드 + QR 텍스트
        d2 = ImageDraw.Draw(out)
        cw = int(size * 0.72)
        x0 = y0 = (size - cw) // 2
        d2.rounded_rectangle((x0, y0, x0 + cw, y0 + cw),
                             radius=int(size * 0.09), fill=(255, 255, 255))
        f = ImageFont.load_default(size=int(size * 0.3))
        tb = d2.textbbox((0, 0), "QR", font=f)
        d2.text(((size - (tb[2] - tb[0])) // 2 - tb[0],
                 (size - (tb[3] - tb[1])) // 2 - tb[1]),
                "QR", fill=(59, 108, 246), font=f)

    if not maskable:
        # 모서리 라운드 처리 (maskable은 전체 채움 유지)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, size - 1, size - 1), radius=int(size * 0.22), fill=255)
        out.putalpha(mask)

    buf = io.BytesIO()
    out.save(buf, format="PNG")
    _ICON_CACHE[key] = png = buf.getvalue()
    return png


@app.get("/icon-192.png")
def icon_192():
    return Response(make_app_icon(192), mimetype="image/png",
                    headers={"Cache-Control": "public, max-age=604800"})


@app.get("/icon-512.png")
def icon_512():
    return Response(make_app_icon(512), mimetype="image/png",
                    headers={"Cache-Control": "public, max-age=604800"})


@app.get("/icon-maskable.png")
def icon_maskable():
    return Response(make_app_icon(512, maskable=True), mimetype="image/png",
                    headers={"Cache-Control": "public, max-age=604800"})


@app.get("/manifest.webmanifest")
def webmanifest():
    return Response(json.dumps(_MANIFEST, ensure_ascii=False),
                    mimetype="application/manifest+json",
                    headers={"Cache-Control": "public, max-age=3600"})


@app.get("/sw.js")
def service_worker_js():
    return Response(_SW_JS, mimetype="application/javascript",
                    headers={"Cache-Control": "no-cache"})


SHARE_PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
__PWA_HEAD__
<title>__NAME__ 님 연락처 QR코드</title>
<style>
  :root {
    --bg: #f4f6fb; --card: #ffffff; --text: #1c2333; --sub: #66708a;
    --accent: #3b6cf6; --accent-press: #2f55c9; --border: #dfe4f0;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #12151d; --card: #1c212e; --text: #eef1f8; --sub: #9aa3bd;
      --border: #2c3346;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px 16px; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Malgun Gothic",
                 "Apple SD Gothic Neo", sans-serif;
    display: flex; justify-content: center;
  }
  .wrap { width: 100%; max-width: 430px; }
  h1 { font-size: 21px; margin: 8px 0 4px; }
  .desc { color: var(--sub); font-size: 14px; margin: 0 0 20px; }
  .card {
    background: var(--card); border: 1px solid var(--border); border-radius: 14px;
    padding: 24px 20px; box-shadow: 0 4px 14px rgba(20, 30, 60, .06);
    text-align: center;
  }
  .qr {
    width: 250px; max-width: 100%; border-radius: 12px;
    border: 1px solid var(--border); background: #fff; display: block;
    margin: 0 auto;
  }
  .who { font-size: 18px; font-weight: 700; margin: 14px 0 2px; }
  .tel { color: var(--sub); font-size: 15px; margin: 0 0 18px; }
  .btns { display: flex; flex-direction: column; gap: 10px; }
  .btn {
    display: block; width: 100%; padding: 15px; font-size: 16.5px; font-weight: 700;
    border-radius: 12px; cursor: pointer; text-align: center;
    text-decoration: none; border: none;
  }
  .btn.primary { color: #fff; background: var(--accent); }
  .btn.primary:active { background: var(--accent-press); }
  .btn.ghost { background: transparent; color: var(--accent); border: 1.5px solid var(--accent); }
  .tip {
    margin-top: 18px; padding: 12px 14px; font-size: 13.5px; line-height: 1.55;
    color: var(--sub); background: var(--bg); border-radius: 10px;
    word-break: keep-all; text-align: left;
  }
  .btnrow2 { display: flex; gap: 10px; margin-top: 10px; }
  .btn.install {
    color: var(--accent); background: var(--bg);
    border: 1.5px dashed var(--accent); font-size: 15px; padding: 13px;
  }
  .overlay {
    position: fixed; inset: 0; background: rgba(15, 20, 34, .55);
    display: none; align-items: center; justify-content: center; padding: 20px;
    z-index: 1000;
  }
  .overlay.open { display: flex; }
  .modal {
    background: var(--card); color: var(--text); width: 100%; max-width: 360px;
    border-radius: 16px; padding: 22px 20px; text-align: left;
    box-shadow: 0 12px 40px rgba(10, 16, 34, .35);
  }
  .modal h3 { margin: 0 0 8px; font-size: 17px; text-align: center; }
  .modal ol { margin: 10px 0 0; padding-left: 20px; font-size: 13.5px; line-height: 1.7; }
  .modal .close {
    margin-top: 16px; width: 100%; padding: 12px; border: none; border-radius: 10px;
    background: var(--accent); color: #fff; font-size: 15px; font-weight: 700; cursor: pointer;
  }
  .appicon {
    width: 56px; height: 56px; border-radius: 14px; display: block; margin: 0 auto 8px;
    box-shadow: 0 3px 10px rgba(20, 30, 60, .25);
  }
  #status { margin-top: 12px; font-size: 14px; min-height: 20px; color: var(--sub); }
  .note { margin-top: 16px; color: var(--sub); font-size: 12.5px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>📇 __NAME__ 님의 연락처 QR</h1>
  <p class="desc">아래 버튼으로 QR코드 이미지를 바로 저장하세요.</p>

  <div class="card">
    <img class="qr" src="__IMG__" alt="연락처 QR코드">
    <div class="who">__NAME__</div>
    <div class="tel">__PHONE__</div>

    <div class="btns">
      <a class="btn primary" href="/qr/__QID__" download="__DLNAME__">⬇️ 이미지 저장</a>
      <button type="button" class="btn ghost" id="shareBtn">↗️ 공유하기</button>
      <div class="btnrow2">
        <button type="button" class="btn install" id="installBtn">📱 앱으로 설치 (바탕화면 추가)</button>
      </div>
    </div>

    <div class="tip">💡 <b>저장이 안 되나요?</b> QR 이미지를 <b>길게 눌러</b> "이미지 저장" 또는 "사진에 추가"를 선택하세요.</div>
    <div id="status"></div>

    <div class="overlay" id="installOverlay">
      <div class="modal" role="dialog" aria-modal="true">
      <img class="appicon" src="/icon-192.png" alt="연락처QR 앱 아이콘">
      <h3>📱 연락처QR 앱으로 설치</h3>
      <ol id="stepGeneric">
        <li>브라우저 메뉴(⋮ 또는 ☰)를 여세요.</li>
        <li><b>[앱 설치]</b> 또는 <b>[홈 화면에 추가]</b>를 선택하세요.</li>
        <li>설치하면 바탕화면에 <b>"연락처QR"</b> 아이콘이 생깁니다.</li>
      </ol>
      <div id="stepIos" style="display:none">
        <ol>
          <li>하단의 <b>공유 버튼</b>(□에 ↑)을 누르세요.</li>
          <li><b>[홈 화면에 추가]</b>를 선택하세요.</li>
          <li>우측 상단 <b>[추가]</b>를 누르면 바탕화면에 설치됩니다.</li>
        </ol>
      </div>
        <button type="button" class="close" id="installClose">닫기</button>
      </div>
    </div>

    <div class="note">이 QR코드를 스마트폰 카메라로 스캔하면 __NAME__ 님의 연락처가 저장됩니다.</div>
  </div>
</div>

<script>
var qid = "__QID__";
var dlName = "__DLNAME__";
var shareBtn = document.getElementById('shareBtn');
var statusEl = document.getElementById('status');
var installBtn = document.getElementById('installBtn');
var installOverlay = document.getElementById('installOverlay');
var installClose = document.getElementById('installClose');
var deferredPrompt = null;
var waitingForPrompt = null;   // 클릭 후 프롬프트 도착을 기다리는 중이면 호출됨

// 네이티브 설치 프롬프트 지원 브라우저(Chrome 등)는 이벤트를 저장해 두었다가 사용
window.addEventListener('beforeinstallprompt', function (e) {
  e.preventDefault();
  deferredPrompt = e;
  if (waitingForPrompt) { waitingForPrompt(); waitingForPrompt = null; }
});
window.addEventListener('appinstalled', function () {
  deferredPrompt = null;
  setStatus('✅ 설치 완료! 바탕화면에서 "연락처QR" 앱을 사용할 수 있어요.');
});

function setStatus(m) { statusEl.textContent = m || ''; }

function copyText(t) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(t);
  }
  return new Promise(function (resolve, reject) {
    var ta = document.createElement('textarea');
    ta.value = t;
    ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus(); ta.select();
    try {
      var ok = document.execCommand('copy');
      ok ? resolve() : reject(new Error('copy failed'));
    } catch (e) { reject(e); }
    finally { ta.remove(); }
  });
}

shareBtn.addEventListener('click', async function () {
  setStatus('공유 준비 중...');
  try {
    var res = await fetch('/qr/' + qid);
    var blob = await res.blob();
    var file = new File([blob], dlName, { type: 'image/png' });
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      await navigator.share({ files: [file], title: dlName.replace(/\\.png$/, '') });
      setStatus('공유했습니다!');
      return;
    }
  } catch (e) {
    if (e && e.name === 'AbortError') { setStatus(''); return; }
  }
  try {
    await copyText(location.href);
    setStatus('링크를 복사했습니다! 메신저로 전달하세요.');
  } catch (e) {
    setStatus('이 브라우저는 공유를 지원하지 않습니다. 이미지 저장 버튼을 이용해 주세요.');
  }
});

// ---- 앱 설치(PWA) ----
function isStandalone() {
  return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
}

// 클릭 시 설치 팝업이 아직 안 왔으면 잠시 기다렸다가 띄움 (원터치 설치)
function waitForPrompt(ms) {
  return new Promise(function (resolve) {
    if (deferredPrompt) { resolve(true); return; }
    var done = false;
    waitingForPrompt = function () { if (!done) { done = true; resolve(true); } };
    setTimeout(function () {
      if (!done) { done = true; waitingForPrompt = null; resolve(false); }
    }, ms);
  });
}

function showInstallGuide() {
  // iOS(사파리)는 네이티브 설치 프롬프트가 없어 공유 메뉴 경로 안내
  var isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) ||
              (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  document.getElementById('stepGeneric').style.display = isIOS ? 'none' : '';
  document.getElementById('stepIos').style.display = isIOS ? '' : 'none';
  installOverlay.classList.add('open');
}

installBtn.addEventListener('click', async function () {
  if (isStandalone()) { setStatus('이미 앱(설치 모드)으로 실행 중입니다.'); return; }
  setStatus('설치 팝업을 준비하는 중...');
  var has = await waitForPrompt(2500);   // 설치 팝업 대기 (최대 2.5초)
  if (has && deferredPrompt) {           // 1) 네이티브 설치 팝업 표시 → 확인 한 번으로 설치
    try {
      deferredPrompt.prompt();
      var choice = await deferredPrompt.userChoice;
      if (choice && choice.outcome === 'accepted') return;  // 완료는 appinstalled에서 안내
      deferredPrompt = null;
      setStatus('설치가 취소되었습니다. 버튼을 다시 누르면 설치할 수 있어요.');
    } catch (_) { deferredPrompt = null; }
    return;
  }
  showInstallGuide();                    // 2) 미지원 환경: 브라우저별 수동 설치 안내
});

installClose.addEventListener('click', function () {
  installOverlay.classList.remove('open');
});

installOverlay.addEventListener('click', function (e) {
  if (e.target === installOverlay) installOverlay.classList.remove('open');
});
</script>
</body>
</html>"""


def build_vcard(name: str, phone: str) -> str:
    """성/이름 분리가 어려우므로 N은 전체 이름을 이름란에 넣고 FN에도 사용 (스마트폰 공용 표준)."""
    return (
        "BEGIN:VCARD\n"
        "VERSION:3.0\n"
        f"N:{name};;;\n"
        f"FN:{name}\n"
        f"TEL;TYPE=CELL:{phone}\n"
        "END:VCARD"
    )


def validate_name(name: str) -> str | None:
    if not name or not name.strip():
        return "이름을 입력해 주세요."
    if len(name) > 30:
        return "이름이 너무 깁니다. (30자 이내)"
    if any(c in name for c in "\r\n"):
        return "이름에 줄바꿈을 사용할 수 없습니다."
    return None


def validate_phone(phone: str) -> tuple[str | None, str]:
    p = re.sub(r"[-\s.]", "", phone or "")
    if not re.fullmatch(r"0\d{9,10}", p):
        return "휴대폰 번호 형식이 올바르지 않습니다. 예: 010-2345-6789", p
    return None, p


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\s]+', "", name) or "contact"


# ---------------------------------------------------------------
# 마지막 생성 QR 영속 저장 — 설치된 앱/바로가기로 열면 즉시 복원 표시
# ---------------------------------------------------------------
LAST_QR_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_qr.json")


def save_last_qr(name: str, phone: str, qid: str, png: bytes) -> None:
    """마지막 생성 QR을 파일로 기록 (서버 재시작 후에도 복원 가능)."""
    try:
        with open(LAST_QR_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "name": name,
                "phone": phone,
                "qid": qid,
                "png_b64": base64.b64encode(png).decode("ascii"),
                "created": datetime.now().isoformat(timespec="seconds"),
            }, f, ensure_ascii=False)
    except OSError:
        pass


def load_last_qr() -> dict | None:
    """저장된 마지막 QR 복원 (파일 없음/손상 시 None)."""
    try:
        with open(LAST_QR_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        png = base64.b64decode(d["png_b64"])
        if not png.startswith(b"\x89PNG"):
            return None
        return {"name": str(d["name"]), "phone": str(d["phone"]),
                "qid": str(d["qid"]), "png": png}
    except (OSError, KeyError, ValueError):
        return None


def register_qr(name: str, phone: str, png: bytes) -> str:
    """공유 링크용 QR 등록 → 짧은 ID 반환."""
    while True:
        qid = secrets.token_urlsafe(6)
        if qid not in QR_STORE:
            break
    if len(QR_STORE) >= MAX_STORE:
        oldest = next(iter(QR_STORE))
        QR_STORE.pop(oldest, None)
    QR_STORE[qid] = {"name": name, "phone": phone, "png": png,
                     "created": datetime.now()}
    save_last_qr(name, phone, qid, png)  # 앱/바로가기 복원용 영속 저장
    return qid


@app.get("/api/last-qr")
def api_last_qr():
    """마지막 생성 QR 조회 — 설치된 앱/바로가기로 열 때 즉시 복원용."""
    item = load_last_qr()
    if not item:
        return jsonify(exists=False)
    return jsonify(
        exists=True,
        name=item["name"],
        phone=item["phone"],
        qid=item["qid"],
        png_b64=base64.b64encode(item["png"]).decode("ascii"),
    )


@app.get("/")
def index() -> Response:
    host = request.host or "127.0.0.1:5000"
    port = host.rsplit(":", 1)[1] if ":" in host else "80"
    lan = f"{get_lan_ip()}:{port}"
    page = (PAGE
            .replace("__LAN__", lan)
            .replace("__PWA_HEAD__", PWA_HEAD)
            .replace("__SW__", _SW_REGISTER))
    return Response(page, mimetype="text/html")


@app.post("/api/qr")
def api_qr():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()

    err = validate_name(name)
    if err:
        return jsonify(error=err), 400
    err, phone_norm = validate_phone(phone)
    if err:
        return jsonify(error=err), 400

    vcard = build_vcard(name, phone_norm)

    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(vcard)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png = buf.getvalue()

    qid = register_qr(name, phone_norm, png)

    # 로컬 백업 저장 (선택적 기록)
    try:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"saved_qrcodes/vcard_{stamp}_{sanitize_filename(name)}.png", "wb") as f:
            f.write(png)
    except OSError:
        pass

    resp = send_file(io.BytesIO(png), mimetype="image/png",
                     download_name=f"vcard_{sanitize_filename(name)}.png")
    resp.headers["X-Qr-Id"] = qid
    return resp


@app.get("/s/<qid>")
def share_page(qid: str):
    """공유 링크 랜딩 페이지: 받은 사람이 여기서 바로 이미지 저장."""
    item = QR_STORE.get(qid)
    if not item:
        return Response(
            "<meta charset='utf-8'><body style=\"font-family:sans-serif;text-align:center;padding:60px\">"
            "<h2>🔗 만료되었거나 잘못된 링크입니다</h2>"
            "<p style='color:#888'>서버를 다시 시작하면 이전 공유 링크는 사용할 수 없습니다.<br>"
            "QR코드를 새로 생성해 주세요.</p></body>",
            mimetype="text/html", status=404,
        )

    img_b64 = base64.b64encode(item["png"]).decode("ascii")
    page = (
        SHARE_PAGE
        .replace("__PWA_HEAD__", PWA_HEAD)
        .replace("__NAME__", html.escape(item["name"]))
        .replace("__PHONE__", html.escape(item["phone"]))
        .replace("__IMG__", f"data:image/png;base64,{img_b64}")
        .replace("__QID__", qid)
        .replace("__DLNAME__", f"vcard_{sanitize_filename(item['name'])}.png")
        .replace("__SW__", _SW_REGISTER)
    )
    return Response(page, mimetype="text/html")


@app.get("/qr/<qid>")
def qr_image(qid: str):
    """QR PNG 직접 다운로드 (공유 페이지의 저장 버튼 대상)."""
    item = QR_STORE.get(qid)
    if not item:
        abort(404)
    return send_file(
        io.BytesIO(item["png"]),
        mimetype="image/png",
        as_attachment=True,
        download_name=f"vcard_{sanitize_filename(item['name'])}.png",
    )


if __name__ == "__main__":
    import threading
    import webbrowser

    url = "http://127.0.0.1:5000"
    print("연락처 QR코드 생성기 시작:", url)
    print(f"스마트폰 접속 (같은 Wi-Fi): http://{get_lan_ip()}:5000")
    print("종료하려면 창을 닫거나 Ctrl+C")

    # 서버 기동 후 브라우저 자동 열기 (자동 테스트 시 QR_NO_BROWSER=1로 비활성)
    if os.environ.get("QR_NO_BROWSER") != "1":
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    app.run(host="0.0.0.0", port=5000, debug=False)
