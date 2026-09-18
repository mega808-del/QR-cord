import qrcode

# 1. 연락처 정보 입력 (갤럭시/아이폰 공용 vCard 표준 규격)
# N: 성;이름;;; 형식으로 입력합니다. (예: 홍;길동;;;)
# FN: 스마트폰 화면에 표시될 전체 이름
# TEL;TYPE=CELL: 휴대폰 전화번호
vcard_data = """BEGIN:VCARD
VERSION:3.0
N:홍;길동;;;
FN:홍길동
TEL;TYPE=CELL:010-2345-6789
END:VCARD"""

# 2. QR코드 생성 설정
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_M,  # 오류 정정 수준 설정
    box_size=10,  # QR코드 박스 크기
    border=4,     # 테두리 여백
)

# 3. 데이터 주입 및 이미지 제작
qr.add_data(vcard_data)
qr.make(fit=True)

# 4. 이미지 파일로 저장
img = qr.make_image(fill_color="black", back_color="white")
img.save("contact_qr_common.png")

print("갤럭시와 아이폰 공용 연락처 QR코드가 'contact_qr_common.png' 파일로 생성되었습니다!")
