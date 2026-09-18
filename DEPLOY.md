# 🚀 GitHub Pages 배포 가이드 — 노트북을 꺼도 24시간 무료 운영

이 프로젝트는 이제 **서버(Flask)가 전혀 필요 없는 순수 정적 사이트**입니다.
QR 생성, 공유 링크, PWA 앱 설치가 모두 브라우저 안에서 동작하므로
GitHub Pages에 올려두기만 하면 노트북이 꺼져 있어도 24시간 무료로 작동합니다.

---

## 1. 무엇이 바뀌었나

| 항목 | 기존 (Flask 서버) | 변경 후 (서버리스) |
|---|---|---|
| QR 생성 | 서버(Python qrcode)가 PNG 생성 | 브라우저 JS(`qrcode.min.js`)가 캔버스에 생성 |
| 공유 링크 | 서버 메모리 `/s/<id>` (재시작 시 만료) | 링크 자체에 데이터 포함 `share.html#...` (**반영구 유효**) |
| 마지막 QR 복원 | 서버 파일(last_qr.json) | 브라우저 localStorage (기기별 복원) |
| 실행 방식 | `python app.py` / `start.bat` | 정적 파일만 서빙 (또는 파일을 직접 열지 않고 배포 URL 접속) |
| 필요 인프라 | 노트북 24시간 켜둠 | GitHub Pages (무료, 무중단) |

- 앱 아이콘: 서버에서 PIL로 동적 생성 → `docs/icon-*.png` 정적 파일로 미리 생성
- 서비스 워커: 정적 아이콘/라이브러리 캐시용으로 그대로 유지 (오프라인 설치 지원)

---

## 2. 배포 방법 (5분)

### 준비물
- GitHub 계정 (무료)

### 2-1. 새 저장소 만들기
1. https://github.com/new 접속
2. Repository name 예: `QR-cord` (또는 원하는 이름)
3. **Public** 선택 (Private은 Pages 무료 사용 불가)
4. [Create repository] 클릭

### 2-2. 프로젝트 업로드
프로젝트 폴더(`C:\Users\HeungPC\Desktop\Project\QR cord`)에서:

```bash
git init
git add docs/
git commit -m "Serverless QR generator for GitHub Pages"
git branch -M main
git remote add origin https://github.com/mega808-del/QR-cord.git
git push -u origin main
```

> 💡 `docs/` 폴더만 배포 대상입니다. `app.py`, `verify_*.py` 등은
> 서버 시절 파일이므로 올려도 무방하지만 Pages에는 사용되지 않습니다.

> ⚠️ 이미 저장소에 파일이 있다면: `git fetch origin && git reset --mixed origin/main`
> 으로 원격 상태와 맞춘 뒤 커밋하면 충돌 없이 올라갑니다.

**실제 배포 주소**: `https://mega808-del.github.io/QR-cord/`

### 2-3. GitHub Pages 켜기
1. 저장소 페이지 → **Settings** → 좌측 **Pages**
2. **Source**: `Deploy from a branch`
3. **Branch**: `main` / **Folder**: `docs` 선택 → **Save**
4. 1~2분 기다리면 주소가 생깁니다:

```
https://mega808-del.github.io/QR-cord/
```

### 2-4. 확인
- 노트북에서 위 주소 접속 → QR 생성 테스트
- 스마트폰(같은 Wi-Fi 아니어도 됨, LTE/5G도 가능)으로 접속 → 설치/공유 테스트
- 이후 노트북을 꺼도 사이트는 계속 작동합니다 ✅

---

## 3. 사용 방법 변화

| 기능 | 사용 방법 |
|---|---|
| QR 생성 | 배포 주소 접속 → 이름/번호 입력 → [QR코드 생성] |
| 공유 | [🔗 공유] 클릭 → 링크 복사 → 메신저 전송. 받은 사람은 링크만 열면 됨 |
| 앱 설치 | [📱 앱으로 설치] → 바탕화면에 "연락처QR" 앱 설치 (PWA) |
| 마지막 QR 복원 | 같은 기기·브라우저에서 다시 열면 자동 복원 |
| 다운로드 | [⬇️ 이미지 저장] |

### 공유 링크 구조 (참고)
```
https://mega808-del.github.io/QR-cord/share.html#1.<vCard>.<이름>.<번호>
```
- 이름·번호·vCard 데이터가 링크 안(base64url)에 들어 있어
- 서버 없이도 링크만으로 QR을 재생성합니다 (만료 없음)
- 단, 번호가 링크에 포함되므로 **신뢰하는 상대에게만 공유**하세요

---

## 4. 기존 서버 버전과의 차이 (한계)

- **QR_STORE 만료 없음**: 기존엔 서버 재시작 시 공유 링크가 죽었지만, 이제 링크는 반영구적
- **복원 범위**: last_qr.json(서버 전역) → localStorage(기기별). 다른 기기에서는 복원되지 않음
- **HTTPS 필수**: PWA 설치/클립보드/공유 API는 HTTPS에서만 동작 → GitHub Pages는 기본 HTTPS라 문제 없음
- **파일로 직접 열기(file://)**: 서비스 워커/클립보드가 제한되므로 권장하지 않음. 로컬 테스트는 아래 방법 사용

### 로컬 테스트 방법 (서버 없이 정적 서빙만)
```bash
cd docs
python -m http.server 8000
# 브라우저에서 http://localhost:8000
```
> 이건 단순 파일 서빙이지 앱 서버가 아닙니다. 배포 후에는 필요 없습니다.

---

## 5. 자주 묻는 질문

**Q. 완전 무료인가요?**
A. GitHub Pages는 공개 저장소 기준 무료이며, 트래픽 제한(월 100GB 소프트 리밋) 안에서 개인 명함 QR 용도로는 충분히 넉넉합니다.

**Q. 커스텀 도메인도 되나요?**
A. 가능합니다. Settings → Pages → Custom domain에서 설정.

**Q. 생성된 QR이 기존 서버 버전과 다르게 생겼어요.**
A. 사용 라이브러리 차이로 모듈(픽셀) 배치 미세 랜덤성(마스크 선택/버전 승격)이 다를 수 있으나,
스캔 결과 데이터(vCard)는 동일하며 jsQR 독립 디코더로 무결성을 검증했습니다.

**Q. 이전 start.bat은?**
A. 이제 더블클릭하면 배포 사이트를 브라우저로 열어줍니다(서버 실행 아님).
