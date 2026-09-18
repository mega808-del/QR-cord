# 📇 연락처 QR코드 생성기 — 작업 내역

> 마지막 업데이트: 2026-09-19
> 프로젝트 위치: `C:\Users\HeungPC\Desktop\Project\QR cord`

---

## 1. 프로젝트 개요

이름과 휴대폰 번호만 입력하면 **갤럭시/아이폰 공용 vCard 3.0 QR코드**를 생성하는 웹 프로그램.
생성된 QR은 **다운로드**하거나 **공유 링크**로 전달할 수 있고, 받은 사람은 모바일에서 원터치 저장이 가능하다.

- **11단계부터 서버리스 전환**: 서버(Flask) 없이 순수 HTML/CSS/JS만으로 동작하며
  GitHub Pages에 배포하면 노트북을 꺼도 24시간 무료 운영된다 (배포 방법은 `DEPLOY.md`).
- 기존 스택(기록용): Python 3.14.7 + Flask 3.1.3 + qrcode 8.2 + pillow 11.3.0 (검증: OpenCV 5.0.0)
- 현재 스택: 정적 사이트 (`docs/`) + [node-qrcode](https://github.com/soldair/node-qrcode) 1.5.4 번들

---

## 2. 파일 구성

| 파일 | 용도 | 상태 |
|---|---|---|
| `docs/index.html` | **메인 페이지** (입력 → QR 생성 → 저장/공유/설치, 서버리스) | ✅ 완성 |
| `docs/share.html` | **공유 링크 수신자 페이지** (해시 payload로 QR 재현) | ✅ 완성 |
| `docs/qrcode.min.js` | node-qrcode 1.5.4 브라우저 번들 (esbuild IIFE, 전역 `QRCode`) | ✅ 검증 완료 |
| `docs/manifest.json` | PWA 매니페스트 (연락처QR, standalone, 상대 경로) | ✅ 완성 |
| `docs/sw.js` | 서비스 워커 (정적 자산 캐시 전용) | ✅ 완성 |
| `docs/icon-192/512/maskable.png` | PWA 앱 아이콘 (기존 PIL 로직으로 사전 생성) | ✅ 완성 |
| `docs/.nojekyll` | GitHub Pages Jekyll 처리 비활성 | ✅ 완성 |
| `DEPLOY.md` | **GitHub Pages 배포 가이드** | ✅ 완성 |
| `start.bat` | 더블클릭 시 **배포 사이트를 브라우저로 열기** (서버 실행 아님) | ✅ 수정 |
| `app.py` | 구 서버 버전 (레거시 보존, 배포에 미사용) | 보존 |
| `generate_contact_qr.py` | 초기 단발성 스크립트 (홍길동 고정) | 보존 |
| `verify_*.py` | 구 서버 자동 검증 테스트들 (서버 시절 기록) | 보존 |
| `saved_qrcodes/` | 구 서버 QR 백업 폴더 (레거시) | 보존 |

---

## 3. 작업 히스토리

### 1단계 — 초기 스크립트 실행
- 사용자가 제공한 vCard QR 생성 스크립트를 `generate_contact_qr.py`로 저장 후 실행
- `qrcode` 모듈 미설치 → `pip install qrcode pillow`로 해결
- `contact_qr_common.png` 생성 성공

### 2단계 — 정상 동작 분석
- OpenCV `QRCodeDetector`로 PNG 디코딩 → **데이터 무결성 100% 일치** 확인
- 발견 사항: `version=1`로 지정했지만 한글 UTF-8(90바이트) 때문에 실제로는 **QR 버전 6**으로 생성됨 (`fit=True`가 자동 승격)
- 개선 제안: `version` 인자 제거, 콘솔 UTF-8 출력 설정

### 3단계 — 웹 앱으로 업그레이드 (`app.py`)
- Flask 기반: 이름/번호 입력 → QR 생성 → 다운로드/공유
- 번호 자동 정규화 (`010-2345-6789`, `010 2345 6789`, `01023456789` 모두 허용 → `01023456789`로 저장)
- 서버 측 입력 검증 (빈 값, 잘못된 번호, 줄바꿈 주입/vCard 변조 차단, 이름 30자 제한)
- 다크모드 지원, 모바일 반응형 UI
- `verify_app.py` 작성 → Flask test client + OpenCV 디코딩 검증

### 4단계 — 공유 링크 기능 추가 (상대방 원터치 저장)
- QR 생성 시 서버 메모리에 등록(`QR_STORE`, 최대 100개 LRU) → 공유 링크 발급
- `GET /s/<id>` : 받은 사람용 모바일 저장 페이지
- `GET /qr/<id>` : PNG 다이렉트 다운로드
- 서버 시작 시 PC 내부 IP 자동 감지 → 스마트폰 접속용 주소 안내

### 5단계 — 더블클릭 실행 (`start.bat`), 6단계 — bat 인코딩 수정
- start.bat을 영문(ASCII) 전용 + CRLF로 재작성 (CP949 깨짐 방지)

### 7~9단계 — PWA 설치/복원 기능 (구 서버 버전)
- PWA 매니페스트/서비스 워커/동적 아이콘, 설치 안내 모달, 마지막 QR 복원(`last_qr.json`)
- 자세한 내용은 git 히스토리 참고

---

## 11단계 — 서버리스 전환 + GitHub Pages 배포 (2026-09-19) ⭐ 현재

**요구**: 노트북을 끄면 서버가 죽어 접속이 안 되는 문제 → 파이썬 서버 없이
HTML/CSS/JS만으로 브라우저에서 동작하게 하고, GitHub Pages로 무료 24시간 배포.

**접근**: 기존 Flask 기능을 하나씩 브라우저 JS로 대체. 기능·디자인은 그대로 유지.

| 구 서버 기능 | 서버리스 대체 |
|---|---|
| `POST /api/qr` (QR PNG 생성) | `QRCode.toDataURL()` — 브라우저 캔버스 생성 |
| `GET /s/<id>` 공유 페이지 | `share.html#1.<vCard>.<이름>.<번호>` (base64url payload, **만료 없음**) |
| `GET /qr/<id>` 다운로드 | `data:` URL + `download` 속성 |
| `GET /api/last-qr` 복원 | `localStorage` (기기별 복원) |
| `/manifest.webmanifest` | `manifest.json` (정적, 상대 경로) |
| `/icon-*.png` PIL 동적 생성 | 사전 생성 정적 파일 |
| `/sw.js` | 정적 `sw.js` (캐시 대상에 `qrcode.min.js` 추가) |

**작업 내용**:
1. **QR 라이브러리 확보**: `qrcode@1.5.4` npm 패키지를 esbuild로 IIFE 번들링
   (전역 `QRCode` 노출). jsdelivr 단일 파일은 CJS `require` 포함으로 브라우저 단독 실행 불가 → 자체 번들 채택
2. **QR 무결성 검증**: 번들이 생성한 QR을 **jsQR(독립 디코더)**로 교차 디코딩 → vCard 데이터 완전 일치 PASS
   - 참고: cv2.QRCodeDetector는 node-qrcode 특유의 반칸(stroke) 렌더링에서 탐지 실패하는 알려진 취약성.
     구 버전(qrcode.py)은 박스 채우기 방식이라 cv2가 잘 읽었을 뿐, 실제 스캔 호환성은 jsQR 검증이 더 실질적
   - Python(qrcode 8.2)과 JS(node-qrcode)는 버전 자동 승격 차이(각각 v6/v5)로 모듈 배치가 다를 수 있으나 스캔 데이터는 동일
3. **`docs/` 정적 사이트 구축**: `index.html`(메인), `share.html`(수신자), `manifest.json`, `sw.js`,
   `.nojekyll`, 아이콘 3종. 디자인(CSS)·버튼 배치·다크모드·설치 모달은 기존과 100% 동일
4. **입력 검증 클라이언트 이식**: 이름 30자/줄바꿈 차단, 번호 정규화(`^0\d{9,10}$`) — 기존 서버 로직과 동일 규칙
5. **`start.bat` 용도 변경**: 서버 실행 → **배포 사이트 열기** (APPURL 수정 필요)
6. **`DEPLOY.md`** 작성: 5분 배포 가이드

**유의사항**:
- 공유 링크에 이름/번호가 포함되므로 신뢰하는 상대에게만 공유 (링크 추정 불가능성은 base64url 수준)
- "마지막 QR 복원"은 서버 전역(`last_qr.json`) → **기기별(localStorage)**로 의미 변화
- PWA/클립보드/공유 API는 HTTPS 필요 → GitHub Pages 기본 HTTPS라 문제 없음
- 로컬 테스트: `cd docs && python -m http.server 8000` (단순 파일 서빙)

---

## 12. GitHub 업로드 참고

- 배포 대상은 **`docs/` 폴더만** (Settings → Pages → Branch: main, Folder: docs)
- `.gitignore`로 `__pycache__/`, `saved_qrcodes/`, `last_qr.json` 제외됨
- PWA 설치 프롬프트는 HTTPS에서 활성화 → Pages 배포 후 모바일에서 최종 확인 권장

## 13. 검증 방법 (재실행용)

```bash
# 번들 무결성 (jsQR 교차 디코딩) — 11단계에서 PASS 확인 완료
# 로컬 정적 서빙 후 브라우저 수동 테스트:
cd docs
python -m http.server 8000
# http://localhost:8000 에서 QR 생성 → 공유 링크 → share.html 복원 확인
```
