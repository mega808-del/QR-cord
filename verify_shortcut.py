# -*- coding: utf-8 -*-
"""설치된 앱/바로가기 시나리오 테스트 — 2회 반복 실행
시나리오: QR 생성 → 페이지/앱 재접속 시 입력폼 없이 QR 즉시 표시
          + 서버 재시작(파일 복원) 후에도 동일하게 표시
주의: 실행 전 반드시 포트 5000의 옛 서버 프로세스를 종료할 것!
      (netstat -ano | findstr :5000 → taskkill /F /PID <pid>)
"""
import base64
import json
import os
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:5000"
HERE = os.path.dirname(os.path.abspath(__file__))
LAST_QR_PATH = os.path.join(HERE, "last_qr.json")
passed, failed = 0, 0


def check(label, cond, extra=""):
    global passed, failed
    mark = "✅" if cond else "❌"
    if cond:
        passed += 1
    else:
        failed += 1
    print(f"  {mark} {label} {extra}")


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return r.status, dict(r.headers), r.read()


def post_json(path, obj):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(obj).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, dict(r.headers), r.read()


def get_page_js_ok():
    """메인 페이지가 복원 스크립트를 포함하는지 확인."""
    _, _, body = get("/")
    return (b"/api/last-qr" in body and b"showRestoredQR" in body
            and b"form.style.display = 'none'" in body)


def run_round(n: int, name: str, phone: str) -> None:
    phone_norm = re.sub(r"[-\s.]", "", phone)  # 서버 번호 정규화 규격과 동일
    print()
    print("=" * 62)
    print(f"테스트 {n}회차: {name} / {phone}")
    print("=" * 62)

    # [1] QR 생성 (입력 → 생성 버튼 시나리오)
    st, hdr, body = post_json("/api/qr", {"name": name, "phone": phone})
    check("POST /api/qr → 200", st == 200)
    check("응답이 PNG", body[:8] == b"\x89PNG\r\n\x1a\n")
    qid = hdr.get("X-Qr-Id")
    check("X-Qr-Id 발급", bool(qid), f"→ {qid}")

    # [2] 앱 아이콘 클릭으로 페이지를 다시 열었다고 가정: GET / 후 last-qr 조회
    check("메인 페이지 복원 스크립트 포함", get_page_js_ok())
    st, _, body = get("/api/last-qr")
    d = json.loads(body.decode("utf-8"))
    check("GET /api/last-qr → exists", st == 200 and d.get("exists") is True)
    check("복원 이름 일치", d.get("name") == name, f"→ {d.get('name')}")
    check("복원 번호 일치(정규화)", d.get("phone") == phone_norm, f"→ {d.get('phone')}")
    check("복원 qid 일치", d.get("qid") == qid)

    png = base64.b64decode(d["png_b64"])
    check("복원 PNG 시그니처", png[:8] == b"\x89PNG\r\n\x1a\n")

    # [3] 복원된 QR 무결성: 실제 디코딩해 vCard 비교
    import cv2
    import numpy as np
    img = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
    decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    expected = (f"BEGIN:VCARD\nVERSION:3.0\nN:{name};;;\\nFN:{name}\n"
                f"TEL;TYPE=CELL:{phone_norm}\nEND:VCARD").replace("\\n", "\n")
    check("복원 QR 디코딩 성공", bool(decoded))
    check("복원 QR vCard 무결성", decoded == expected)

    # [4] 복원 상태에서 다운로드 경로(/qr/<id>) 확인
    st, hdr2, body2 = get(f"/qr/{qid}")
    check("복원 상태 다운로드 → 200", st == 200)
    check("복원 상태 PNG 동일", body2 == png)

    # [5] 서버 재시작 시나리오: 파일이 실제로 남는지 (디스크 검증)
    ok_file = os.path.exists(LAST_QR_PATH)
    check("last_qr.json 파일 생성됨", ok_file)
    if ok_file:
        with open(LAST_QR_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        check("파일 내 이름/번호 일치",
              saved.get("name") == name and saved.get("phone") == phone_norm)


def main():
    # 서버 구동 확인
    try:
        get("/")
    except OSError:
        print("❌ 서버(127.0.0.1:5000)가 실행 중이 아닙니다. python app.py 후 재실행하세요.")
        sys.exit(1)

    run_round(1, "이상호", "01056630101")
    run_round(2, "홍길동", "010-2345-6789")   # 번호 정규화 포함 2회차

    # 2회차가 1회차를 덮어쓰는지(최신 1건 유지) 확인
    _, _, body = get("/api/last-qr")
    d = json.loads(body.decode("utf-8"))
    check("2회차 생성 후 last-qr가 최신으로 갱신", d.get("name") == "홍길동")

    print()
    print(f"결과: {passed} 통과 / {failed} 실패")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
