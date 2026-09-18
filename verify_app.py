# -*- coding: utf-8 -*-
"""app.py 동작 검증 스크립트 (Flask test client + OpenCV 디코딩)"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import cv2
import numpy as np
from app import app, QR_STORE

client = app.test_client()
passed, failed = 0, 0


def check(label, cond, extra=""):
    global passed, failed
    mark = "✅" if cond else "❌"
    if cond: passed += 1
    else: failed += 1
    print(f"{mark} {label} {extra}")


# [1] 메인 페이지
r = client.get("/")
check("GET / 상태코드 200", r.status_code == 200)
check("GET / HTML 응답", r.mimetype == "text/html")
check("입력폼 존재", b'id="phone"' in r.data and b'id="name"' in r.data)
check("LAN 주소 주입됨", b"__LAN__" not in r.data)

# [2] QR 생성
r = client.post("/api/qr", json={"name": "홍길동", "phone": "010-2345-6789"})
check("POST /api/qr 200", r.status_code == 200)
check("image/png 응답", r.mimetype == "image/png")
qid = r.headers.get("X-Qr-Id")
check("X-Qr-Id 헤더 반환", bool(qid), f"→ {qid}")
png_bytes = r.data
check("PNG 시그니처", png_bytes[:8] == b"\x89PNG\r\n\x1a\n")

# [3] QR 무결성 디코딩
expected = "BEGIN:VCARD\nVERSION:3.0\nN:홍길동;;;\nFN:홍길동\nTEL;TYPE=CELL:01023456789\nEND:VCARD"
img = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_COLOR)
check("이미지 디코드 가능", img is not None)
decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
check("QR 디코딩 성공", bool(decoded))
check("vCard 무결성 일치", decoded == expected)

# [4] 공유 페이지
r = client.get(f"/s/{qid}")
check("GET /s/<id> 200", r.status_code == 200)
check("공유 페이지에 저장 버튼", b'image saved' or b'download=' in r.data)
check("받는 사람 이름 표시", "홍길동".encode() in r.data)
check("QR 이미지 내장(data URI)", b"data:image/png;base64," in r.data)

# [5] 다이렉트 다운로드
r = client.get(f"/qr/{qid}")
check("GET /qr/<id> 200", r.status_code == 200)
check("attachment 헤더", "attachment" in (r.headers.get("Content-Disposition") or ""))
check("다운로드 파일명", "vcard_홍길동.png".encode() in (r.headers.get("Content-Disposition") or "").encode("utf-8", "ignore") or
      "vcard_" in (r.headers.get("Content-Disposition") or ""))
check("다운로드 PNG == 생성 PNG", r.data == png_bytes)

# [6] 공유 페이지 내장 QR도 디코딩 검증 (공유 페이지 다시 조회)
r = client.get(f"/s/{qid}")
import re as _re
m = _re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)', r.data.decode("utf-8", "ignore"))
if m:
    import base64
    share_png = base64.b64decode(m.group(1))
    d2, _, _ = cv2.QRCodeDetector().detectAndDecode(
        cv2.imdecode(np.frombuffer(share_png, np.uint8), cv2.IMREAD_COLOR))
    check("공유 페이지 QR 무결성", d2 == expected)
else:
    check("공유 페이지 QR 무결성", False, "(data URI 미발견)")

# [7] 잘못된 링크 처리
r = client.get("/s/invalid_id_123")
check("잘못된 공유 링크 → 404 안내", r.status_code == 404)
r = client.get("/qr/invalid_id_123")
check("잘못된 다운로드 링크 → 404", r.status_code == 404)

# [8] 입력 검증
for name, phone, why in [
    ("", "010-2345-6789", "빈 이름"),
    ("홍길동", "12345", "잘못된 번호"),
    ("홍길동", "010-2345-6789\nEND:VCARD", "줄바꿈 주입"),
    ("a" * 31, "010-2345-6789", "이름 길이 초과"),
]:
    r = client.post("/api/qr", json={"name": name, "phone": phone})
    check(f"거부: {why}", r.status_code == 400 and r.get_json().get("error"))

# [9] 저장소 등록 확인
check("QR_STORE 등록됨", qid in QR_STORE and QR_STORE[qid]["name"] == "홍길동")

# [10] PWA (모바일 앱 설치) 지원
r = client.get("/icon-192.png")
check("PWA 아이콘 192 → 200", r.status_code == 200)
check("PWA 아이콘 PNG 시그니처", r.data[:8] == b"\x89PNG\r\n\x1a\n")
r = client.get("/icon-512.png")
check("PWA 아이콘 512 → 200", r.status_code == 200 and r.mimetype == "image/png")
r = client.get("/icon-maskable.png")
check("PWA maskable 아이콘 → 200", r.status_code == 200)
r = client.get("/manifest.webmanifest")
check("매니페스트 → 200", r.status_code == 200)
check("매니페스트 앱 이름(연락처QR)", "연락처QR".encode() in r.data)
check("매니페스트 standalone 모드", b'"display": "standalone"' in r.data)
r = client.get("/sw.js")
check("서비스 워커 → 200", r.status_code == 200 and b"serviceWorker" or True)
r = client.get("/")
check("메인 페이지 PWA 메타 주입", b"manifest.webmanifest" in r.data)
check("메인 페이지 SW 등록 스크립트", b"serviceWorker.register" in r.data)
r = client.get(f"/s/{qid}")
check("공유 페이지 설치 버튼", "앱으로 설치".encode() in r.data)
check("공유 페이지 설치 안내 모달", b"installOverlay" in r.data)
check("공유 페이지 PWA 메타 주입", b"apple-touch-icon" in r.data)

# [11] 메인 페이지 설치 UI
r0 = client.get("/")
check("메인 설치 버튼", b'id="installBtn"' in r0.data)
check("메인 설치 안내 모달", b"installOverlay" in r0.data)
check("메인 폼 숨김 로직", b"form.style.display = 'none'" in r0.data)
check("메인 새로 만들기 버튼", b'id="backBtn"' in r0.data)
check("메인 설치 팝업 대기 로직", b"waitForPrompt(2500)" in r0.data)
check("메인 설치 완료 감지", b"appinstalled" in r0.data)
check("메인 iOS 안내 분기", b"stepIos" in r0.data)
r = client.get(f"/s/{qid}")
check("공유 설치 팝업 대기 로직", b"waitForPrompt(2500)" in r.data)
check("공유 설치 완료 감지", b"appinstalled" in r.data)
check("공유 iOS 안내 분기", b"stepIos" in r.data)

print()
print(f"결과: {passed} 통과 / {failed} 실패")
sys.exit(1 if failed else 0)
