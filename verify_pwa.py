# -*- coding: utf-8 -*-
"""PWA 설치 요건 종합 검증 — 실제 서버에 HTTP로 접속해 확인"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:5000"
passed, failed = 0, 0


def check(label, cond, extra=""):
    global passed, failed
    mark = "✅" if cond else "❌"
    if cond:
        passed += 1
    else:
        failed += 1
    print(f"{mark} {label} {extra}")


def get(path):
    req = urllib.request.Request(BASE + path)
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, dict(r.headers), r.read()


print("=" * 60)
print("[1] PWA 설치 필수 요건 (Chrome 기준)")
print("=" * 60)

st, hdr, body = get("/manifest.webmanifest")
check("매니페스트 응답 200", st == 200)
check("Content-Type = manifest", "manifest" in hdr.get("Content-Type", ""))
m = json.loads(body.decode("utf-8"))
check("앱 이름 = 연락처QR", m.get("short_name") == "연락처QR")
check("display = standalone", m.get("display") == "standalone")
check("start_url 지정", bool(m.get("start_url")))
icons = m.get("icons", [])
sizes = {i.get("sizes") for i in icons}
check("192px 아이콘 존재", "192x192" in sizes)
check("512px 아이콘 존재", "512x512" in sizes)
check("maskable 아이콘 존재", any(i.get("purpose") == "maskable" for i in icons))

st, _, body = get("/")
check("메인 페이지에 manifest 링크", b'manifest.webmanifest' in body)
check("메인 페이지 SW 등록 코드", b"serviceWorker.register" in body)
check("메인 페이지 설치 버튼", b'id="installBtn"' in body)
check("theme-color 메타 존재", b"theme-color" in body)

print()
print("=" * 60)
print("[2] 아이콘/서비스워커 실제 로드")
print("=" * 60)

for path in ("/icon-192.png", "/icon-512.png", "/icon-maskable.png"):
    st, hdr, body = get(path)
    ok_png = body[:8] == b"\x89PNG\r\n\x1a\n"
    check(f"{path} 로드", st == 200 and ok_png, f"({len(body)} bytes)")

st, hdr, body = get("/sw.js")
check("sw.js 로드", st == 200)
check("sw.js 캐시 로직 포함", b"addEventListener('fetch'" in body)

print()
print("=" * 60)
print("[3] 아이콘 이미지 유효성 (PIL 재파싱)")
print("=" * 60)

import io

from PIL import Image

for path, size in (("/icon-192.png", 192), ("/icon-512.png", 512), ("/icon-maskable.png", 512)):
    _, _, body = get(path)
    img = Image.open(io.BytesIO(body))
    img.load()
    check(f"{path} 유효 이미지", img.size == (size, size), f"→ {img.size} {img.mode}")

print()
print(f"결과: {passed} 통과 / {failed} 실패")
sys.exit(1 if failed else 0)
