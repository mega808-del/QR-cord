# -*- coding: utf-8 -*-
"""generate_contact_qr.py 정상 동작 검증 스크립트 (분석용)"""
import sys, io
sys.stdout.reconfigure(encoding="utf-8")

import qrcode
from qrcode.util import QRData, MODE_8BIT_BYTE

print("=" * 60)
print("[1] 환경 정보")
print("=" * 60)
print("qrcode 버전:", getattr(qrcode, "__version__", "unknown"))
print("Python:", sys.version.split()[0])

# ---------------------------------------------------------------
print()
print("=" * 60)
print("[2] 스크립트와 동일한 설정으로 QR 재생성 → 내부 상태 점검")
print("=" * 60)
vcard_data = """BEGIN:VCARD
VERSION:3.0
N:홍;길동;;;
FN:홍길동
TEL;TYPE=CELL:010-2345-6789
END:VCARD"""

qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    box_size=10,
    border=4,
)
qr.add_data(vcard_data)
qr.make(fit=True)

n_bytes = len(vcard_data.encode("utf-8"))
data_len_bits = 4 + (n_bytes * 8)  # 8bit byte 모드: 4bit 모드지시자 + 데이터
version_capacity_M = {1: 14, 2: 26, 3: 42, 4: 62}  # v1~v4 M 오류정정 byte 용량

print("vCard 데이터 바이트 수 (UTF-8):", n_bytes)
print("필요 비트 수 (모드지시자 포함):", data_len_bits)
print("QR 버전 (fit 결과):", qr.version)
print(f"버전{qr.version} + M 오류정정 byte 용량:", version_capacity_M.get(qr.version, "?"), "bytes")
print("버전1(M) 강제 지정 시 용량: 14 bytes → 한글 때문에 초과 → fit=True 덕분에 자동 승격됨")
print("모듈 크기:", qr.modules_count, "x", qr.modules_count)
print("border 포함 최종 이미지 픽셀:", (qr.modules_count + 2 * 4) * 10, "px")

# ---------------------------------------------------------------
print()
print("=" * 60)
print("[3] 실제 저장된 PNG 파일 디코딩 검증 (OpenCV QRCodeDetector)")
print("=" * 60)
import cv2
import numpy as np

img = cv2.imread("contact_qr_common.png")
assert img is not None, "contact_qr_common.png 파일을 읽을 수 없음!"
print("이미지 크기 (h x w):", img.shape[0], "x", img.shape[1])

det = cv2.QRCodeDetector()
decoded, points, _ = det.detectAndDecode(img)

if decoded:
    print("디코딩 성공!")
    print("-" * 60)
    print(decoded)
    print("-" * 60)
    # 원본 데이터와 정확히 일치하는지 검증
    match = (decoded == vcard_data)
    print("원본 vCard 데이터와 일치:", match)
    if match:
        print("→ 데이터 무결성 100% 확인 (한글 인코딩 UTF-8 왕복 성공)")
    # vCard 필드별 파싱 확인
    print()
    print("[4] vCard 필드 파싱 점검 (스마트폰이 읽을 구조)")
    for line in decoded.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            print(f"  {key:<16} = {val}")
else:
    print("디코딩 실패: QR을 감지하지 못했거나 패턴을 읽지 못함")
    sys.exit(1)
